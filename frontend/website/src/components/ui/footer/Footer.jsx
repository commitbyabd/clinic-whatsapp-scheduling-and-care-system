import { Link } from "react-router";
import {
  footerColumns,
  footerContact,
  footerDescription,
  footerLegal,
} from "../../../data/components/footer/FooterData";
import {
  COMPANY_NAME,
  COMPANY_TAGLINE,
  LOGO_HEIGHT,
  LOGO_ON_DARK_SRC,
  LOGO_WIDTH,
} from "../../../utils/global/Constants";
import { externalLinkProps } from "../../../utils/global/Links";
import Container from "../container/Container";
import styles from "./footer.module.css";
import { getLinkKind } from "./FooterUtils";

function FooterLink({ item }) {
  const kind = getLinkKind(item);

  if (kind === "route") {
    return (
      <Link to={item.path} className={styles.link}>
        {item.label}
      </Link>
    );
  }

  if (kind === "external") {
    return (
      <a
        href={item.href}
        className={styles.link}
        {...externalLinkProps(item.href)}
      >
        {item.label}
      </a>
    );
  }

  return <span className={styles.linkText}>{item.label}</span>;
}

function Footer() {
  return (
    <footer className={styles.footer}>
      <Container>
        <div className={styles.columns}>
          <div className={styles.brand}>
            <Link to="/" className={styles.lockup}>
              <img
                src={LOGO_ON_DARK_SRC}
                alt={`${COMPANY_NAME} — ${COMPANY_TAGLINE}`}
                className={styles.logo}
                width={LOGO_WIDTH}
                height={LOGO_HEIGHT}
                loading="lazy"
                decoding="async"
              />
            </Link>
            <p className={styles.brandCopy}>{footerDescription}</p>
          </div>

          {footerColumns.map((column) => (
            <div key={column.id}>
              <h2 className={styles.columnHeading}>{column.heading}</h2>
              <div className={styles.columnLinks}>
                {column.links.map((item) => (
                  <FooterLink key={item.id} item={item} />
                ))}
              </div>
            </div>
          ))}

          <div>
            <h2 className={styles.columnHeading}>{footerContact.heading}</h2>
            <address className={styles.columnLinks}>
              {footerContact.items.map((item) =>
                item.lines ? (
                  <span key={item.id} className={styles.linkText}>
                    {item.lines.map((line, index) => (
                      <span key={line}>
                        {line}
                        {index < item.lines.length - 1 ? <br /> : null}
                      </span>
                    ))}
                  </span>
                ) : (
                  <a
                    key={item.id}
                    href={item.href}
                    className={styles.link}
                    {...externalLinkProps(item.href)}
                  >
                    {item.label}
                  </a>
                ),
              )}
            </address>
          </div>
        </div>

        <div className={styles.legal}>
          <span>{footerLegal.copyright}</span>
          <span className={styles.legalItems}>
            {footerLegal.items.map((item) => (
              <span key={item.id}>{item.label}</span>
            ))}
          </span>
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
