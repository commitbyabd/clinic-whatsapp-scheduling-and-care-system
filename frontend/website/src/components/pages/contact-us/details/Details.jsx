import {
  detailsData,
  hoursData,
  mapData,
} from "../../../../data/pages/contact-us/details/DetailsData";
import Container from "../../../ui/container/Container";
import LazyImage from "../../../ui/lazy-image/LazyImage";
import PhotoPlaceholder from "../../../ui/photo-placeholder/PhotoPlaceholder";
import Reveal from "../../../ui/reveal/Reveal";
import ContactForm from "../contact-form/ContactForm";
import HoursList from "./_components/HoursList";
import InfoCard from "./_components/InfoCard";
import styles from "./details.module.css";

function Details() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.layout}>
          <div className={styles.stack}>
            <div className={styles.cards}>
              {detailsData.map((detail) => (
                <InfoCard key={detail.id} {...detail} />
              ))}

              <InfoCard label={hoursData.label}>
                <HoursList rows={hoursData.rows} />
              </InfoCard>
            </div>

            {mapData.src ? (
              <LazyImage
                src={mapData.src}
                alt={mapData.label}
                className={styles.map}
              />
            ) : (
              <PhotoPlaceholder
                tone="sage"
                label={mapData.label}
                className={styles.map}
                caption={
                  <>
                    {mapData.caption}
                    <br />
                    {mapData.captionDetail}
                  </>
                }
              />
            )}
          </div>

          <ContactForm />
        </Reveal>
      </Container>
    </section>
  );
}

export default Details;
