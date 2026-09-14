#!/usr/bin/env python3
"""
predict.py — standalone command line / interactive inference.

    python predict.py "itching, skin rash, nodal skin eruptions"
    python predict.py --json "high fever, headache, vomiting"
    python predict.py --metrics              # show accuracy/F1 from training
    python predict.py                        # interactive REPL

Runs entirely on its own (no shared package, no imports from train.py /
serve.py) — everything needed to load model.joblib and predict is defined in
this file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

try:  # Windows consoles default to a codepage that can't print unicode bars below
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SPLIT = re.compile(r"[,\n;/|]+|\s+and\s+")

# --------------------------------------------------------------------------
# Text normalisation + fuzzy matching
# --------------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(text: str) -> str:
    """Lowercase, strip punctuation/underscores/spaces -> canonical key.

    'Skin Rash' -> 'skin_rash'; ' dischromic _patches' -> 'dischromic_patches'
    """
    s = str(text).strip().lower()
    s = _NON_ALNUM.sub("_", s)
    return s.strip("_")


def _squash(text: str) -> str:
    """Remove all separators entirely -> 'skinrash'. Used for loose matching."""
    return normalize(text).replace("_", "")


@dataclass
class SymptomMatch:
    """Result of resolving one user-supplied string to the vocabulary."""

    raw: str
    matched: str | None
    score: float
    method: str  # exact | squashed | token | fuzzy | none

    @property
    def ok(self) -> bool:
        return self.matched is not None


class SymptomVocabulary:
    """Resolves arbitrary user text to canonical symptom names."""

    def __init__(self, symptoms: Sequence[str], synonyms: dict[str, str] | None = None):
        self.symptoms: list[str] = list(symptoms)
        self.index: dict[str, int] = {s: i for i, s in enumerate(self.symptoms)}
        self._squashed: dict[str, str] = {_squash(s): s for s in self.symptoms}
        self._tokens: dict[str, set[str]] = {
            s: set(normalize(s).split("_")) for s in self.symptoms
        }
        self.synonyms: dict[str, str] = {
            normalize(k): v for k, v in (synonyms or {}).items()
        }
        self._fuzzy_pool: dict[str, str] = {_squash(s): s for s in self.symptoms}
        for alias, target in self.synonyms.items():
            t = normalize(target)
            if t in self.index:
                self._fuzzy_pool.setdefault(_squash(alias), t)

    def __len__(self) -> int:
        return len(self.symptoms)

    def resolve(self, raw: str, cutoff: float = 0.78) -> SymptomMatch:
        key = normalize(raw)
        if not key:
            return SymptomMatch(raw, None, 0.0, "none")

        if key in self.synonyms:
            key = normalize(self.synonyms[key])

        if key in self.index:
            return SymptomMatch(raw, key, 1.0, "exact")

        sq = key.replace("_", "")
        if sq in self._squashed:
            return SymptomMatch(raw, self._squashed[sq], 0.99, "squashed")

        toks = set(key.split("_"))
        best_tok, best_tok_score = None, 0.0
        for sym, stoks in self._tokens.items():
            if not stoks:
                continue
            inter = len(toks & stoks)
            if inter == 0:
                continue
            score = inter / len(stoks | toks)
            if score > best_tok_score:
                best_tok, best_tok_score = sym, score
        if best_tok_score >= 0.75:
            return SymptomMatch(raw, best_tok, best_tok_score, "token")

        best_f, best_fs = None, 0.0
        for cand, target in self._fuzzy_pool.items():
            s = SequenceMatcher(None, sq, cand).ratio()
            if s > best_fs:
                best_f, best_fs = target, s
        if best_fs >= cutoff:
            return SymptomMatch(raw, best_f, best_fs, "fuzzy")

        if best_tok_score >= 0.45:
            return SymptomMatch(raw, best_tok, best_tok_score, "token")

        return SymptomMatch(raw, None, best_fs, "none")

    def resolve_many(self, raws: Iterable[str], cutoff: float = 0.78) -> list[SymptomMatch]:
        seen, out = set(), []
        for r in raws:
            m = self.resolve(r, cutoff=cutoff)
            if m.ok and m.matched in seen:
                continue
            if m.ok:
                seen.add(m.matched)
            out.append(m)
        return out

    def suggest(self, prefix: str, limit: int = 10) -> list[str]:
        """Autocomplete helper for a UI search box."""
        p = normalize(prefix).replace("_", "")
        if not p:
            return self.symptoms[:limit]
        starts = [s for s in self.symptoms if _squash(s).startswith(p)]
        contains = [s for s in self.symptoms if p in _squash(s) and s not in starts]
        rest = sorted(
            (s for s in self.symptoms if s not in starts and s not in contains),
            key=lambda s: -SequenceMatcher(None, p, _squash(s)).ratio(),
        )
        return (starts + contains + rest)[:limit]

    def encode(self, symptoms: Iterable[str]) -> np.ndarray:
        vec = np.zeros(len(self.symptoms), dtype=np.int8)
        for s in symptoms:
            i = self.index.get(s)
            if i is not None:
                vec[i] = 1
        return vec


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


@dataclass
class Prediction:
    disease: str
    probability: float

    def as_dict(self) -> dict:
        return {"disease": self.disease, "probability": round(self.probability, 4),
                "percent": round(self.probability * 100, 2)}


# ============================================================================
# OPTIONAL ADD-ON: disease -> specialist percentages.
# Self-contained (its own dataclass, loader, and DiseaseModel method) so this
# whole section — and every call site marked the same way below — can be
# deleted or commented out without touching disease prediction at all.
# ============================================================================

@dataclass
class SpecializationPrediction:
    specialization: str
    probability: float

    def as_dict(self) -> dict:
        return {"specialization": self.specialization, "probability": round(self.probability, 4),
                "percent": round(self.probability * 100, 2)}


def load_specialization_map(path: str | Path) -> dict[str, str]:
    """Disease -> recommended specialist, from a 2-column CSV (Disease, Specialization).

    Returns {} (never raises) if the file is missing so the rest of the
    script keeps working even without it.
    """
    import csv

    path = Path(path)
    if not path.exists():
        return {}
    mapping: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            disease = (row.get("Disease") or "").strip()
            spec = (row.get("Specialization") or "").strip()
            if disease and spec:
                mapping[disease] = spec
    return mapping

# ============================================================================
# END OPTIONAL ADD-ON (part 1/2 — see DiseaseModel.predict_specializations
# and print_specializations below for the rest)
# ============================================================================


# ============================================================================
# OPTIONAL ADD-ON: symptom severity scoring. Self-contained — safe to delete
# this whole section and its call sites without touching disease prediction.
# ============================================================================

def load_severity_map(path: str | Path) -> dict[str, int]:
    """Symptom -> severity weight (1-7), from a 2-column CSV (Symptom, weight).

    Returns {} (never raises) if the file is missing.
    """
    import csv

    path = Path(path)
    if not path.exists():
        return {}
    mapping: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = normalize(row.get("Symptom") or "")
            try:
                w = int(str(row.get("weight") or "").strip())
            except ValueError:
                continue
            if sym:
                mapping[sym] = w
    return mapping


def severity_assessment(recognized: Sequence[str], severity_map: dict[str, int],
                         high_threshold: int = 6) -> dict:
    """Score reported symptoms by severity weight; flag high-severity ones.

    Returns {} if there is no severity map or none of the recognized symptoms
    have a known weight (dataset quirk: a couple of symptom names in the
    severity CSV don't exactly match the vocabulary and are silently skipped).
    """
    if not severity_map or not recognized:
        return {}
    scored = [(s, severity_map[s]) for s in recognized if s in severity_map]
    if not scored:
        return {}
    total = sum(w for _, w in scored)
    return {
        "symptoms": [{"symptom": s, "weight": w} for s, w in scored],
        "total_score": total,
        "average_score": round(total / len(scored), 2),
        "high_severity_symptoms": [s for s, w in scored if w >= high_threshold],
    }

# ============================================================================
# END OPTIONAL ADD-ON
# ============================================================================


# ============================================================================
# OPTIONAL ADD-ON: disease precautions. Self-contained — safe to delete this
# whole section and its call sites without touching disease prediction.
# ============================================================================

def load_precaution_map(path: str | Path) -> dict[str, list[str]]:
    """Disease -> list of precautions, from a Disease,Precaution_1..4 CSV.

    Returns {} (never raises) if the file is missing.
    """
    import csv

    path = Path(path)
    if not path.exists():
        return {}
    mapping: dict[str, list[str]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            disease = (row.get("Disease") or "").strip()
            if not disease:
                continue
            precs = [
                v.strip() for k, v in row.items()
                if k and k.lower().startswith("precaution") and v and v.strip()
            ]
            mapping[disease] = precs
    return mapping

# ============================================================================
# END OPTIONAL ADD-ON
# ============================================================================


@dataclass
class PredictionResult:
    predictions: list[Prediction]
    recognized: list[str]
    unrecognized: list[str]
    corrections: list[dict] = field(default_factory=list)
    warning: str | None = None

    def as_dict(self) -> dict:
        return {
            "predictions": [p.as_dict() for p in self.predictions],
            "recognized_symptoms": self.recognized,
            "unrecognized_input": self.unrecognized,
            "corrections": self.corrections,
            "warning": self.warning,
            "disclaimer": (
                "Informational only. This is a statistical pattern match over "
                "reported symptoms, not a medical diagnosis. Consult a clinician."
            ),
        }


class DiseaseModel:
    """Ensemble of RandomForest + BernoulliNB over multi-hot symptoms."""

    VERSION = "1.0.0"

    def __init__(
        self,
        vocabulary: SymptomVocabulary,
        rf_weight: float = 0.5,
        random_state: int = 42,
    ):
        self.vocab = vocabulary
        self.rf_weight = rf_weight
        self.random_state = random_state
        self.rf = None
        self.nb = None
        self.classes_: list[str] = []
        self.canonical: dict[str, list[frozenset[str]]] = {}
        self.metrics: dict = {}

    def _matrix(self, symptom_sets: Sequence[frozenset[str]]) -> np.ndarray:
        X = np.zeros((len(symptom_sets), len(self.vocab)), dtype=np.int8)
        idx = self.vocab.index
        for i, s in enumerate(symptom_sets):
            for sym in s:
                j = idx.get(sym)
                if j is not None:
                    X[i, j] = 1
        return X

    def _proba(self, X: np.ndarray) -> np.ndarray:
        p_rf = self.rf.predict_proba(X)
        p_nb = self.nb.predict_proba(X)
        if list(self.nb.classes_) != list(self.rf.classes_):
            order = [list(self.nb.classes_).index(c) for c in self.rf.classes_]
            p_nb = p_nb[:, order]
        return self.rf_weight * p_rf + (1.0 - self.rf_weight) * p_nb

    def predict_proba_sets(self, symptom_sets: Sequence[frozenset[str]]) -> np.ndarray:
        return self._proba(self._matrix(symptom_sets))

    def predict(
        self,
        raw_symptoms: Iterable[str],
        top_k: int = 5,
        min_probability: float = 0.03,
        fuzzy_cutoff: float = 0.78,
    ) -> PredictionResult:
        """Main production entry point. Accepts free text, any case, any count."""
        matches = self.vocab.resolve_many(raw_symptoms, cutoff=fuzzy_cutoff)
        recognized = [m.matched for m in matches if m.ok]
        unrecognized = [m.raw for m in matches if not m.ok]
        corrections = [
            {"input": m.raw, "matched_to": m.matched,
             "confidence": round(m.score, 3), "method": m.method}
            for m in matches
            if m.ok and m.method != "exact"
        ]

        if not recognized:
            return PredictionResult(
                predictions=[], recognized=[], unrecognized=unrecognized,
                corrections=corrections,
                warning="No input matched the known symptom vocabulary.",
            )

        X = self._matrix([frozenset(recognized)])
        proba = self._proba(X)[0]

        order = np.argsort(proba)[::-1]
        preds = [
            Prediction(self.classes_[i], float(proba[i]))
            for i in order[:top_k]
            if proba[i] >= min_probability
        ]
        if not preds:
            preds = [Prediction(self.classes_[order[0]], float(proba[order[0]]))]

        warning = None
        if len(recognized) == 1:
            warning = ("Only one symptom recognised — results are weakly "
                       "constrained. Add more symptoms for a useful ranking.")
        elif preds[0].probability < 0.25:
            warning = ("Low confidence: the reported symptoms do not match any "
                       "single known pattern well.")
        if unrecognized:
            extra = f"Unrecognised input ignored: {', '.join(unrecognized)}."
            warning = f"{warning} {extra}" if warning else extra

        return PredictionResult(preds, recognized, unrecognized, corrections, warning)

    # ------------------------------------------------------------------
    # OPTIONAL ADD-ON (part 2/2): specialist percentages. Independent of
    # predict() above — safe to delete this method and its call sites
    # without changing disease prediction behaviour at all.
    # ------------------------------------------------------------------
    def predict_specializations(
        self,
        raw_symptoms: Iterable[str],
        specialization_map: dict[str, str],
        top_k: int = 5,
        min_probability: float = 0.0,
        fuzzy_cutoff: float = 0.78,
    ) -> list["SpecializationPrediction"]:
        """Same symptom resolution as predict(), but aggregates the FULL
        probability distribution (not just the top-k diseases) by specialist
        so percentages reflect the whole prediction, not only what's shown."""
        if not specialization_map:
            return []
        matches = self.vocab.resolve_many(raw_symptoms, cutoff=fuzzy_cutoff)
        recognized = [m.matched for m in matches if m.ok]
        if not recognized:
            return []

        proba = self._proba(self._matrix([frozenset(recognized)]))[0]
        totals: dict[str, float] = {}
        for i, disease in enumerate(self.classes_):
            spec = specialization_map.get(disease, "Unknown")
            totals[spec] = totals.get(spec, 0.0) + float(proba[i])

        ranked = sorted(totals.items(), key=lambda kv: -kv[1])
        return [
            SpecializationPrediction(spec, p)
            for spec, p in ranked[:top_k]
            if p >= min_probability
        ]
    # ------------------------------------------------------------------
    # END OPTIONAL ADD-ON
    # ------------------------------------------------------------------

    def explain(self, disease: str, recognized: Sequence[str]) -> dict:
        """Which reported symptoms support this disease, and what's missing."""
        sets = self.canonical.get(disease, [])
        if not sets:
            return {"disease": disease, "matched": [], "missing": [], "coverage": 0.0}
        best = max(sets, key=lambda s: len(s & set(recognized)))
        matched = sorted(set(recognized) & best)
        missing = sorted(best - set(recognized))
        return {
            "disease": disease,
            "matched_symptoms": matched,
            "typical_symptoms_not_reported": missing,
            "coverage": round(len(matched) / len(best), 3) if best else 0.0,
        }

    @classmethod
    def load(cls, path: str | Path) -> "DiseaseModel":
        import joblib

        blob = joblib.load(path)
        vocab = SymptomVocabulary(blob["symptoms"], blob.get("synonyms"))
        m = cls(vocab, rf_weight=blob.get("rf_weight", 0.5))
        m.rf = blob["rf"]
        m.nb = blob["nb"]
        m.classes_ = blob["classes"]
        m.canonical = {k: [frozenset(s) for s in v] for k, v in blob["canonical"].items()}
        m.metrics = blob.get("metrics", {})
        return m


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse(text: str) -> list[str]:
    return [p.strip() for p in SPLIT.split(text) if p.strip()]


def print_metrics(metrics: dict) -> None:
    """Pretty-print accuracy (top1/top3) and macro-F1 stored on the model."""
    if not metrics:
        print("No metrics stored on this model — retrain with train.py to generate them.")
        return
    print("Accuracy and F1 score (from cross-validation at training time):")
    for regime, m in metrics.items():
        print(
            f"  {regime:<18} accuracy(top1)={m['top1']['mean']:.3f}±{m['top1']['std']:.3f}  "
            f"accuracy(top3)={m['top3']['mean']:.3f}  f1(macro)={m['macro_f1']['mean']:.3f}"
        )


def show(model, result, explain=False):
    if not result.predictions:
        print(f"  {result.warning}")
        if result.unrecognized:
            print("  Did you mean:",
                  ", ".join(model.vocab.suggest(result.unrecognized[0], 5)))
        return
    if result.corrections:
        for c in result.corrections:
            print(f"  interpreted '{c['input']}' as '{c['matched_to']}' "
                  f"({c['method']}, {c['confidence']})")
    print(f"  using: {', '.join(result.recognized)}\n")
    width = max(len(p.disease) for p in result.predictions)
    for p in result.predictions:
        bar = "█" * int(round(p.probability * 30))
        print(f"  {p.disease.ljust(width)}  {p.probability*100:6.2f}%  {bar}")
    if result.warning:
        print(f"\n  ! {result.warning}")
    if explain:
        for p in result.predictions[:3]:
            e = model.explain(p.disease, result.recognized)
            print(f"\n  {p.disease}: matched {e['matched_symptoms']}")
            print(f"    typically also seen: {e['typical_symptoms_not_reported']}")
            print(f"    coverage of typical presentation: {e['coverage']*100:.0f}%")


# ---- OPTIONAL ADD-ON: specialist percentages display (safe to comment out) ----
def print_specializations(specializations: list) -> None:
    """Bar-chart display for recommended-specialist percentages, mirrors show()."""
    if not specializations:
        return
    print("\n  Recommended specialist:")
    width = max(len(s.specialization) for s in specializations)
    for s in specializations:
        bar = "█" * int(round(s.probability * 30))
        print(f"    {s.specialization.ljust(width)}  {s.probability*100:6.2f}%  {bar}")
# ---- END OPTIONAL ADD-ON ----


# ---- OPTIONAL ADD-ON: severity display (safe to comment out) ----
def print_severity(severity: dict) -> None:
    if not severity:
        return
    print(f"\n  Reported severity — total: {severity['total_score']}, "
          f"average: {severity['average_score']}")
    if severity["high_severity_symptoms"]:
        print(f"    high-severity symptoms: {', '.join(severity['high_severity_symptoms'])}")
# ---- END OPTIONAL ADD-ON ----


# ---- OPTIONAL ADD-ON: precautions display (safe to comment out) ----
def print_precautions(result, precaution_map: dict) -> None:
    if not precaution_map or not result.predictions:
        return
    for p in result.predictions[:3]:
        precs = precaution_map.get(p.disease)
        if precs:
            print(f"\n  Precautions for {p.disease}: {', '.join(precs)}")
# ---- END OPTIONAL ADD-ON ----


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symptoms", nargs="*", help="comma separated symptoms")
    ap.add_argument("--model", default="model.joblib")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--min-prob", type=float, default=0.03)
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--metrics", action="store_true",
                    help="print accuracy/F1 score stored on the model and exit")
    ap.add_argument("--specialization-map", default="disease_specialization_mapping.csv",
                    help="CSV mapping disease -> recommended specialist (optional add-on)")
    ap.add_argument("--severity-map", default="symptom_severity.csv",
                    help="CSV mapping symptom -> severity weight (optional add-on)")
    ap.add_argument("--precaution-map", default="symptom_precaution.csv",
                    help="CSV mapping disease -> precautions (optional add-on)")
    args = ap.parse_args()

    model = DiseaseModel.load(args.model)

    if args.metrics:
        if args.json:
            print(json.dumps(model.metrics, indent=2))
        else:
            print_metrics(model.metrics)
        return

    # ---- OPTIONAL ADD-ON: load specialist/severity/precaution maps (safe to comment out) ----
    specialization_map = load_specialization_map(args.specialization_map)
    severity_map = load_severity_map(args.severity_map)
    precaution_map = load_precaution_map(args.precaution_map)
    # ---- END OPTIONAL ADD-ON ----

    if args.symptoms:
        items = parse(" , ".join(args.symptoms))
        r = model.predict(items, top_k=args.top_k, min_probability=args.min_prob)

        # ---- OPTIONAL ADD-ON: specialist/severity/precautions (safe to comment out) ----
        specializations = model.predict_specializations(
            items, specialization_map, top_k=args.top_k
        )
        severity = severity_assessment(r.recognized, severity_map)
        # ---- END OPTIONAL ADD-ON ----

        if args.json:
            out = r.as_dict()
            if args.explain:
                out["explanations"] = [model.explain(p.disease, r.recognized)
                                       for p in r.predictions]
            # ---- OPTIONAL ADD-ON (safe to comment out) ----
            if specializations:
                out["specializations"] = [s.as_dict() for s in specializations]
            if severity:
                out["severity"] = severity
            if precaution_map:
                out["precautions"] = {
                    p.disease: precaution_map[p.disease]
                    for p in r.predictions if p.disease in precaution_map
                }
            # ---- END OPTIONAL ADD-ON ----
            print(json.dumps(out, indent=2))
        else:
            show(model, r, args.explain)
            # ---- OPTIONAL ADD-ON: safe to comment out ----
            print_specializations(specializations)
            print_severity(severity)
            print_precautions(r, precaution_map)
            # ---- END OPTIONAL ADD-ON ----
        return

    print(f"Loaded {len(model.classes_)} diseases, {len(model.vocab)} symptoms.")
    print("Enter symptoms separated by commas. '?<text>' to search. Ctrl-D to quit.\n")
    while True:
        try:
            line = input("symptoms> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.startswith("?"):
            print("  ", ", ".join(model.vocab.suggest(line[1:], 12)))
            continue
        items = parse(line)
        r = model.predict(items, top_k=args.top_k, min_probability=args.min_prob)
        show(model, r, args.explain)
        # ---- OPTIONAL ADD-ON: specialist/severity/precautions (safe to comment out) ----
        print_specializations(model.predict_specializations(items, specialization_map, top_k=args.top_k))
        print_severity(severity_assessment(r.recognized, severity_map))
        print_precautions(r, precaution_map)
        # ---- END OPTIONAL ADD-ON ----
        print()


if __name__ == "__main__":
    main()
