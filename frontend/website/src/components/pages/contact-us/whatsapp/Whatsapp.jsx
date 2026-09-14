import {
  whatsappChat,
  whatsappData,
} from "../../../../data/pages/contact-us/whatsapp/WhatsappData";
import Button from "../../../ui/button/Button";
import ChatMock from "../../../ui/chat-mock/ChatMock";
import Chip from "../../../ui/chip/Chip";
import Container from "../../../ui/container/Container";
import styles from "./whatsapp.module.css";

function Whatsapp() {
  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.block}>
          <div>
            <Chip variant="translucent" size="lg" dot>
              {whatsappData.badge}
            </Chip>

            <h2 className={styles.heading}>{whatsappData.heading}</h2>
            <p className={styles.description}>{whatsappData.description}</p>

            <div className={styles.actions}>
              <Button
                href={whatsappData.cta.href}
                variant="whiteOnSage"
                target="_blank"
                rel="noopener"
              >
                {whatsappData.cta.label}
              </Button>

              <span className={styles.phone}>{whatsappData.phone}</span>
            </div>
          </div>

          <ChatMock
            variant="card"
            title={whatsappChat.title}
            status={whatsappChat.status}
            label={whatsappChat.label}
            messages={whatsappChat.messages}
          />
        </div>
      </Container>
    </section>
  );
}

export default Whatsapp;
