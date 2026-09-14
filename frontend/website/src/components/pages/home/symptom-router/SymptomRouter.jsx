import { useId, useRef, useState } from "react";
import {
  DEFAULT_SYMPTOM_INDEX,
  symptomRouterData,
  symptomRoutes,
} from "../../../../data/pages/home/symptom-router/SymptomRouterData";
import { ROUTES } from "../../../../utils/global/Constants";
import Button from "../../../ui/button/Button";
import Container from "../../../ui/container/Container";
import styles from "./symptom-router.module.css";
import { nextRadioIndex } from "./SymptomRouterUtils";

/**
 * The site's one genuinely interactive element. State is a single integer,
 * local to this component — it does not persist and does not reach the URL.
 *
 * This is navigation, not triage: it points at a department, never at a
 * diagnosis.
 */
function SymptomRouter() {
  const [selected, setSelected] = useState(DEFAULT_SYMPTOM_INDEX);
  const chipRefs = useRef([]);
  const groupLabelId = useId();

  const route = symptomRoutes[selected];

  const handleKeyDown = (event) => {
    const next = nextRadioIndex(event.key, selected, symptomRoutes.length);
    if (next === null) return;

    event.preventDefault();
    setSelected(next);
    chipRefs.current[next]?.focus();
  };

  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.block}>
          <div>
            <p className={styles.eyebrow}>{symptomRouterData.eyebrow}</p>
            <h2 className={styles.heading}>{symptomRouterData.heading}</h2>
            <p className={styles.description}>
              {symptomRouterData.description}
            </p>
            <p className={styles.emergency}>
              {symptomRouterData.emergencyNote}
            </p>
          </div>

          <div className={styles.panel}>
            <p className={styles.panelLabel} id={groupLabelId}>
              {symptomRouterData.chipsLabel}
            </p>

            <div
              className={styles.chips}
              role="radiogroup"
              aria-labelledby={groupLabelId}
              onKeyDown={handleKeyDown}
            >
              {symptomRoutes.map((symptom, index) => {
                const isSelected = index === selected;

                return (
                  <button
                    key={symptom.id}
                    type="button"
                    role="radio"
                    aria-checked={isSelected}
                    tabIndex={isSelected ? 0 : -1}
                    ref={(node) => {
                      chipRefs.current[index] = node;
                    }}
                    className={`${styles.chip} ${
                      isSelected ? styles.chipSelected : ""
                    }`.trim()}
                    onClick={() => setSelected(index)}
                  >
                    {symptom.label}
                  </button>
                );
              })}
            </div>

            <div className={styles.result}>
              {/* Announced so a screen-reader user hears the department
                  change as they move through the chips. */}
              <div aria-live="polite">
                <p className={styles.resultLabel}>
                  {symptomRouterData.resultLabel}
                </p>
                <p className={styles.department}>{route.department}</p>
                <p className={styles.note}>{route.note}</p>
              </div>

              <Button
                to={`${ROUTES.contact}?dept=${route.slug}`}
                variant="primary"
                className={styles.cta}
              >
                {symptomRouterData.cta}
              </Button>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}

export default SymptomRouter;
