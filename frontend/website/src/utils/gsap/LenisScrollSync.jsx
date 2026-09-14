import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useLenis } from "lenis/react";
import { useEffect } from "react";

gsap.registerPlugin(ScrollTrigger);

/**
 * Drives Lenis from GSAP's ticker so smooth scrolling and ScrollTrigger
 * share a single frame loop. Requires <ReactLenis options={{ autoRaf: false }} />
 * so Lenis does not also run its own requestAnimationFrame.
 */
function LenisScrollSync() {
  const lenis = useLenis(() => ScrollTrigger.update());

  useEffect(() => {
    if (!lenis) return undefined;

    const raf = (time) => lenis.raf(time * 1000);

    gsap.ticker.add(raf);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(raf);
      gsap.ticker.lagSmoothing(500, 33);
    };
  }, [lenis]);

  return null;
}

export default LenisScrollSync;
