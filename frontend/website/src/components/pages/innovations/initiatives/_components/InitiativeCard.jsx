import ChatMock from "../../../../ui/chat-mock/ChatMock";
import Chip from "../../../../ui/chip/Chip";
import LazyImage from "../../../../ui/lazy-image/LazyImage";
import styles from "./InitiativeCard.module.css";
import RecordList from "./RecordList";
import ResearchStats from "./ResearchStats";

function InitiativeMedia({ media }) {
  if (media.type === "chat") {
    return (
      <ChatMock
        variant="tray"
        label={media.label}
        messages={media.messages}
        className={styles.media}
      />
    );
  }

  if (media.type === "stats") {
    return (
      <div className={styles.media}>
        <ResearchStats items={media.items} />
      </div>
    );
  }

  if (media.type === "records") {
    return (
      <div className={styles.media}>
        <RecordList rows={media.rows} />
      </div>
    );
  }

  return (
    <LazyImage
      src={media.src}
      alt={media.alt}
      className={`${styles.media} ${styles.image}`}
    />
  );
}

function InitiativeCard({ index, theme, status, title, description, media, footnote }) {
  return (
    <article
      className={`${styles.card} ${styles[theme]} ${
        media.hideOnMobile ? styles.mediaHiddenOnMobile : ""
      }`.trim()}
    >
      <div className={styles.head}>
        <span className={styles.index}>{index}</span>
        <Chip variant={status.variant}>{status.label}</Chip>
      </div>

      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>

      <InitiativeMedia media={media} />

      <p className={styles.footnote}>{footnote}</p>
    </article>
  );
}

export default InitiativeCard;
