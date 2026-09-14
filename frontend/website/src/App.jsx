import { ReactLenis } from "lenis/react";
import IconProvider from "./components/ui/icon/IconProvider";
import ScrollToTop from "./components/ui/scroll-to-top/ScrollToTop";
import ProjectRoutes from "./routes/ProjectRoutes";
import LenisScrollSync from "./utils/gsap/LenisScrollSync";

function App() {
  return (
    <IconProvider>
      <ReactLenis root options={{ autoRaf: false }}>
        <LenisScrollSync />
        <ScrollToTop />
        <ProjectRoutes />
      </ReactLenis>
    </IconProvider>
  );
}

export default App;
