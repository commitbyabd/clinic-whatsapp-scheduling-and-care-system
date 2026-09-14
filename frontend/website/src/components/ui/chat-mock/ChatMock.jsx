import styles from "./chat-mock.module.css";

/**
 * An illustration of a conversation, not live UI — so the whole thing is a
 * single role="img" with a descriptive label and the bubbles are hidden from
 * assistive tech.
 *
 * `tray` is the bare bubble tray on the Innovations booking card; `card` is
 * the titled assistant window on the Contact page.
 */
function ChatMock({
  messages = [],
  label,
  variant = "tray",
  title,
  status,
  className = "",
  ...rest
}) {
  return (
    <div
      className={`${styles.mock} ${styles[variant]} ${className}`.trim()}
      role="img"
      aria-label={label}
      {...rest}
    >
      {title ? (
        <div className={styles.header} aria-hidden="true">
          <span className={styles.avatar} />
          <span className={styles.title}>{title}</span>
          {status ? <span className={styles.status}>{status}</span> : null}
        </div>
      ) : null}

      {messages.map((message) => (
        <p
          key={message.id}
          className={`${styles.bubble} ${styles[message.from]}`}
          aria-hidden="true"
        >
          {message.text}
        </p>
      ))}
    </div>
  );
}

export default ChatMock;
