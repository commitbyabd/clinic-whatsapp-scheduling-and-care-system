import { whoWeAreData } from "../../../../data/pages/home/who-we-are/WhoWeAreData";
import Container from "../../../ui/container/Container";
import LazyImage from "../../../ui/lazy-image/LazyImage";
import PhotoPlaceholder from "../../../ui/photo-placeholder/PhotoPlaceholder";
import Reveal from "../../../ui/reveal/Reveal";
import SectionIntro from "../../../ui/section-intro/SectionIntro";
import styles from "./who-we-are.module.css";

function WhoWeAre() {
  const { author } = whoWeAreData;

  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.grid}>
          <SectionIntro
            eyebrow={whoWeAreData.eyebrow}
            heading={whoWeAreData.heading}
            headingWidth={340}
            className={styles.intro}
          />

          <div className={styles.body}>
            {whoWeAreData.paragraphs.map((paragraph) => (
              <p key={paragraph.id} className={styles.paragraph}>
                {paragraph.text}
              </p>
            ))}

            <div className={styles.author}>
              {author.photo ? (
                <LazyImage
                  src={author.photo}
                  alt={`${author.name}, ${author.role}`}
                  className={styles.authorPhoto}
                />
              ) : (
                <PhotoPlaceholder
                  band={8}
                  label={author.photoLabel}
                  className={styles.authorPhoto}
                />
              )}

              <div>
                <p className={styles.authorName}>{author.name}</p>
                <p className={styles.authorRole}>{author.role}</p>
              </div>
            </div>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default WhoWeAre;
