import { useLenis } from "lenis/react";
import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router";
import { navCta, navItems } from "../../../data/components/nav/NavData";
import {
  COMPANY_NAME,
  COMPANY_TAGLINE,
  LOGO_HEIGHT,
  LOGO_SRC,
  LOGO_WIDTH,
} from "../../../utils/global/Constants";
import Button from "../button/Button";
import Container from "../container/Container";
import styles from "./nav.module.css";
import { bindEscape, isActivePath, lockScroll, unlockScroll } from "./NavUtils";

function Nav() {
  const { pathname } = useLocation();
  const lenis = useLenis();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [openedOn, setOpenedOn] = useState(pathname);

  /* Any route change — a drawer link, or the browser's back button —
     closes the drawer. Adjusted during render rather than in an effect so
     the drawer never paints over the new page for a frame. */
  if (isMenuOpen && openedOn !== pathname) {
    setIsMenuOpen(false);
  }
  if (openedOn !== pathname) {
    setOpenedOn(pathname);
  }

  useEffect(() => {
    if (!isMenuOpen) return undefined;

    lockScroll(lenis);
    const releaseEscape = bindEscape(() => setIsMenuOpen(false));

    return () => {
      releaseEscape();
      unlockScroll(lenis);
    };
  }, [isMenuOpen, lenis]);

  return (
    <>
      <header className={styles.header}>
        <Container className={styles.bar}>
          {/* logo.avif is the full lockup — mark, name and tagline — so it
              replaces the text lockup rather than sitting beside it. The
              wording lives on in the alt text. */}
          <Link to="/" className={styles.lockup}>
            <img
              src={LOGO_SRC}
              alt={`${COMPANY_NAME} — ${COMPANY_TAGLINE}`}
              className={styles.logo}
              width={LOGO_WIDTH}
              height={LOGO_HEIGHT}
            />
          </Link>

          <nav className={styles.nav} aria-label="Primary">
            {navItems.map((item) => (
              <Link
                key={item.id}
                to={item.path}
                className={`${styles.pill} ${
                  isActivePath(pathname, item.path) ? styles.pillActive : ""
                }`.trim()}
                aria-current={
                  isActivePath(pathname, item.path) ? "page" : undefined
                }
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <Button to={navCta.path} variant="gold" size="sm" className={styles.cta}>
            {navCta.label}
          </Button>

          <button
            type="button"
            className={styles.burger}
            onClick={() => setIsMenuOpen((open) => !open)}
            aria-expanded={isMenuOpen}
            aria-controls="mobile-menu"
            aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          >
            <span className={styles.burgerBar} />
            <span className={styles.burgerBar} />
          </button>
        </Container>
      </header>

      {/* The drawer lives outside <header>: the header's backdrop-filter
          makes it a containing block, which would collapse a fixed child. */}
      <div
        id="mobile-menu"
        className={`${styles.drawer} ${isMenuOpen ? styles.drawerOpen : ""}`.trim()}
        hidden={!isMenuOpen}
      >
        <nav className={styles.drawerNav} aria-label="Primary, mobile">
          {navItems.map((item) => (
            <Link
              key={item.id}
              to={item.path}
              className={`${styles.drawerLink} ${
                isActivePath(pathname, item.path) ? styles.drawerLinkActive : ""
              }`.trim()}
              aria-current={
                isActivePath(pathname, item.path) ? "page" : undefined
              }
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <Button
          to={navCta.path}
          variant="gold"
          size="lg"
          className={styles.drawerCta}
        >
          {navCta.label}
        </Button>
      </div>
    </>
  );
}

export default Nav;
