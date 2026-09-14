import gsap from "gsap";
import { useLayoutEffect, useRef } from "react";

/**
 * Kicks off any lazy image inside a block that has just been revealed.
 *
 * A lazily-loaded image only starts downloading when the browser decides it
 * is near the viewport, and that decision is confused by the transform this
 * component applies while the block animates in — images at the end of a
 * revealed group could be left permanently unloaded, showing an empty box.
 *
 * This only ever runs on a block that has finished revealing, so by
 * definition these images are on screen and should be loading anyway.
 */
const loadPendingImages = (root) => {
  root.querySelectorAll('img[loading="lazy"]').forEach((image) => {
    if (!image.complete) image.loading = "eager";
  });
};

/**
 * The site's only motion: a single fade-up as a block enters the viewport.
 * The handoff is explicit that the design's calm depends on restraint, so
 * there is no scroll-linked animation anywhere else.
 *
 * Entry is detected with IntersectionObserver rather than ScrollTrigger.
 * ScrollTrigger caches element positions when the trigger is created, which
 * on this site happens before the page's lazy images have loaded — so the
 * cached positions go stale the moment those images size themselves and a
 * block can end up never revealed. IntersectionObserver is recomputed by
 * the browser continuously, so it cannot desync.
 *
 * Only opacity and transform are animated. autoAlpha would be tidier, but
 * it sets visibility:hidden, and the browser will not load lazy images
 * inside a hidden subtree — which is what made the stale positions fatal
 * rather than merely late.
 *
 * Under prefers-reduced-motion nothing is ever hidden: the effect returns
 * before setting the start state.
 *
 * There is intentionally no will-change. It used to be set permanently, which
 * pinned every revealed block to its own GPU layer for the life of the page
 * after a 400ms animation — memory pressure that, together with oversized
 * portraits, left the last nurse portraits unpainted. The browser promotes
 * the layer for the duration of the tween on its own.
 */
function Reveal({
  as: Tag = "div",
  delay = 0,
  distance,
  className = "",
  children,
  ...rest
}) {
  const ref = useRef(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return undefined;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return undefined;
    }

    const shift =
      distance ??
      parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue(
          "--reveal-distance",
        ),
      ) ??
      18;

    gsap.set(element, { opacity: 0, y: shift });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;

          observer.unobserve(entry.target);
          gsap.to(entry.target, {
            opacity: 1,
            y: 0,
            duration: 0.4,
            delay,
            ease: "power2.out",
            clearProps: "transform",
            onComplete: () => loadPendingImages(entry.target),
          });
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0 },
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
      gsap.killTweensOf(element);
      gsap.set(element, { clearProps: "opacity,transform" });
    };
  }, [delay, distance]);

  return (
    <Tag ref={ref} className={className || undefined} {...rest}>
      {children}
    </Tag>
  );
}

export default Reveal;
