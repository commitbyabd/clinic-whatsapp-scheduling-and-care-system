import {
  STATUS_FEED_URL,
  statusBoardData,
} from "../../../../data/pages/home/status-board/StatusBoardData";
import useJsonFeed from "../../../../hooks/useJsonFeed";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import StatusCell from "./_components/StatusCell";
import styles from "./status-board.module.css";
import { formatUpdatedAt } from "./StatusBoardUtils";

/**
 * Near-real-time operational board, fed by a JSON document the front desk
 * edits without a rebuild.
 *
 * The whole section is hidden when the feed is missing or empty: a stale or
 * zeroed board does more damage than no board at all.
 *
 * No aria-live here — the feed is read once on mount and does not update
 * in-session, so announcing it would be a lie.
 */
function StatusBoard() {
  const { status, data } = useJsonFeed(STATUS_FEED_URL);

  const cells = Array.isArray(data?.cells) ? data.cells : [];
  if (status !== "ready" || cells.length === 0) return null;

  const updatedAt = formatUpdatedAt(data.updatedAt);

  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.head}>
          <div>
            <p className={styles.eyebrow}>
              <span className={styles.eyebrowDot} aria-hidden="true" />
              {statusBoardData.eyebrow}
            </p>
            <h2 className={styles.heading}>{statusBoardData.heading}</h2>
          </div>

          <p className={styles.support}>{statusBoardData.description}</p>
        </div>

        <Reveal className={styles.board}>
          {cells.map((cell) => (
            <StatusCell key={cell.id} {...cell} />
          ))}
        </Reveal>

        {updatedAt ? (
          <p className={styles.updated}>
            {statusBoardData.updatedLabel} {updatedAt}
          </p>
        ) : null}
      </Container>
    </section>
  );
}

export default StatusBoard;
