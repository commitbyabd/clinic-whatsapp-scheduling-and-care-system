import { Route, Routes } from "react-router";
import RootLayout from "../layouts/RootLayout";
import AboutUs from "../pages/about-us/AboutUs";
import ContactUs from "../pages/contact-us/ContactUs";
import Home from "../pages/home/Home";
import Innovations from "../pages/innovations/Innovations";
import NotFound from "../pages/not-found/NotFound";
import OurTeam from "../pages/our-team/OurTeam";

function ProjectRoutes() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/about-us" element={<AboutUs />} />
        <Route path="/our-team" element={<OurTeam />} />
        <Route path="/innovations" element={<Innovations />} />
        <Route path="/contact-us" element={<ContactUs />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default ProjectRoutes;
