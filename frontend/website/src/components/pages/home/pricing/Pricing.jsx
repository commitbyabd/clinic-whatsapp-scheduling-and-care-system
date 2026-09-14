import {
  pricingData,
  pricingIntro,
} from "../../../../data/pages/home/pricing/PricingData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import PriceCard from "./_components/PriceCard";
import styles from "./pricing.module.css";

function Pricing() {
  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.head}>
          <div>
            <p className={styles.eyebrow}>{pricingIntro.eyebrow}</p>
            <h2 className={styles.heading}>{pricingIntro.heading}</h2>
          </div>

          <p className={styles.support}>{pricingIntro.description}</p>
        </div>

        <Reveal className={styles.grid}>
          {pricingData.map((item) => (
            <PriceCard key={item.id} {...item} />
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

export default Pricing;
