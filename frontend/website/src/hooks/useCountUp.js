import gsap from "gsap";
import { useLayoutEffect, useRef } from "react";

/**
 * Counts a figure up from zero the first time it scrolls into view.
 *
 * Returns a ref for the element that shows the number. The number is written
 * straight to that element's text rather than through React state, so the
 * animation does not re-render the component sixty times a second — which is
 * why that element should have no React children of its own.
 *
 * Accessibility: the animating element should be aria-hidden, with the final
 * value available to screen readers separately. A reader hearing every
 * intermediate figure is noise, not information.
 *
 * Under prefers-reduced-motion the final value is shown immediately.
 */
function useCountUp({ to, decimals = 0, duration = 1.8 }) {
  const ref = useRef(null);

  useLayoutEffect(() => {
    const node = ref.current;
    if (!node) return undefined;

    const format = (value) => value.toFixed(decimals);
    const showFinal = () => {
      node.textContent = format(to);
    };

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      showFinal();
      return undefined;
    }

    /* Set before first paint, so the final figure never flashes up first. */
    node.textContent = format(0);

    const counter = { value: 0 };
    let tween = null;

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;

        observer.disconnect();
        tween = gsap.to(counter, {
          value: to,
          duration,
          ease: "power2.out",
          onUpdate: () => {
            node.textContent = format(counter.value);
          },
          onComplete: showFinal,
        });
      },
      { threshold: 0.4 },
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
      tween?.kill();
      showFinal();
    };
  }, [to, decimals, duration]);

  return ref;
}

export default useCountUp;
