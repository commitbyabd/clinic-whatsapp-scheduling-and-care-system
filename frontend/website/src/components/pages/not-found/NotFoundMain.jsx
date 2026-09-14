import { notFoundData } from "../../../data/not-found/NotFoundData";
import Button from "../../ui/button/Button";
import Container from "../../ui/container/Container";
import SectionIntro from "../../ui/section-intro/SectionIntro";
import styles from "./not-found-main.module.css";

function NotFoundMain() {
  return (
    <section className={styles.section}>
      <Container>
        <SectionIntro
          as="h1"
          align="center"
          eyebrow={notFoundData.eyebrow}
          heading={notFoundData.heading}
          description={notFoundData.description}
          descriptionWidth={520}
        >
          <div className={styles.actions}>
            <Button to={notFoundData.primary.path} variant="primary">
              {notFoundData.primary.label}
            </Button>
            <Button to={notFoundData.secondary.path} variant="outline">
              {notFoundData.secondary.label}
            </Button>
          </div>
        </SectionIntro>
      </Container>
    </section>
  );
}

export default NotFoundMain;
