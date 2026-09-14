import {
  clinicDaysColumns,
  clinicDaysData,
  clinicDaysFootnote,
  clinicDaysIntro,
} from "../../../../data/pages/our-team/clinic-days/ClinicDaysData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import styles from "./clinic-days.module.css";

/**
 * The visual reads as a grid of inset pills, but the content is tabular, so
 * this is a real <table> with column headers. The pill rows come from
 * rounding the first and last cell of each row rather than from overriding
 * the table's display, which would strip the semantics a screen reader
 * needs.
 */
function ClinicDays() {
  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.head}>
          <div>
            <p className={styles.eyebrow}>{clinicDaysIntro.eyebrow}</p>
            <h2 className={styles.heading}>{clinicDaysIntro.heading}</h2>
          </div>

          <p className={styles.support}>{clinicDaysIntro.description}</p>
        </div>

        <Reveal className={styles.card}>
          <table className={styles.table}>
            <caption className="srOnly">
              Clinic days by department, with lead clinician, OPD days and
              theatre days.
            </caption>

            <colgroup>
              <col className={styles.colDepartment} />
              <col className={styles.colLead} />
              <col className={styles.colDays} />
              <col className={styles.colTheatre} />
            </colgroup>

            <thead>
              <tr className={styles.headRow}>
                {clinicDaysColumns.map((column) => (
                  <th key={column.id} scope="col" className={styles.th}>
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {clinicDaysData.map((row, index) => (
                <tr
                  key={row.id}
                  className={`${styles.row} ${
                    index % 2 === 1 ? styles.rowStriped : ""
                  }`.trim()}
                >
                  <th scope="row" className={styles.department}>
                    {row.name}
                  </th>

                  <td className={styles.lead}>
                    <a href={`#${row.leadDoctorId}`} className={styles.leadLink}>
                      {row.leadName}
                    </a>
                  </td>

                  <td className={styles.days}>{row.opdDays}</td>
                  <td className={styles.theatre}>{row.theatreDays}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Reveal>

        <p className={`${styles.footnote} ${styles.footnoteFull}`}>
          {clinicDaysFootnote.full}
        </p>
        <p className={`${styles.footnote} ${styles.footnoteShort}`}>
          {clinicDaysFootnote.short}
        </p>
      </Container>
    </section>
  );
}

export default ClinicDays;
