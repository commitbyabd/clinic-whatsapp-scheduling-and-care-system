/* Reads the design tokens straight off :root at runtime so variables.css
   stays the single source of truth — even for colors handed to JS-driven
   animation. Fallbacks match variables.css and only apply before hydration. */

export const getCssVar = (name, fallback = "") => {
  if (typeof window === "undefined" || !document.documentElement) {
    return fallback;
  }

  const value = getComputedStyle(document.documentElement).getPropertyValue(
    name,
  );

  return value.trim() || fallback;
};

export const Colors = {
  /* Surfaces */
  get creamBase() {
    return getCssVar("--cream-base", "#f6f1e9");
  },
  get creamCard() {
    return getCssVar("--cream-card", "#fffcf6");
  },
  get sand() {
    return getCssVar("--sand", "#efe7d8");
  },
  get creamInk() {
    return getCssVar("--cream-ink", "#fff9ef");
  },

  /* Ink */
  get ink() {
    return getCssVar("--ink", "#2e2a26");
  },
  get inkBody() {
    return getCssVar("--ink-body", "#5b5349");
  },
  get inkEyebrow() {
    return getCssVar("--ink-eyebrow", "#a2947f");
  },

  /* Accents — sage is the institution, terracotta is the Fund,
     gold is the ask. Never swap their jobs. */
  get sage() {
    return getCssVar("--sage", "#6e8672");
  },
  get sagePale() {
    return getCssVar("--sage-pale", "#e4eae1");
  },
  get terracotta() {
    return getCssVar("--terracotta", "#c4837a");
  },
  get gold() {
    return getCssVar("--gold", "#c08a3e");
  },

  /* Borders */
  get borderSoft() {
    return getCssVar("--border-soft", "#ede1cf");
  },
  get borderRule() {
    return getCssVar("--border-rule", "#e7dccb");
  },
  get borderStrong() {
    return getCssVar("--border-strong", "#d6c9b4");
  },
};

/* Ordered color sets for animation — index-driven, so the order here
   controls the visual rhythm. */
export const animationColors = {
  accents: () => [Colors.sage, Colors.terracotta, Colors.gold],
  surfaces: () => [Colors.creamCard, Colors.sand, Colors.sagePale],
};
