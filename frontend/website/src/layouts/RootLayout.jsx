import { Outlet } from "react-router";
import Footer from "../components/ui/footer/Footer";
import Nav from "../components/ui/nav/Nav";

function RootLayout() {
  return (
    <>
      <Nav />
      <main>
        <Outlet />
      </main>
      <Footer />
    </>
  );
}

export default RootLayout;
