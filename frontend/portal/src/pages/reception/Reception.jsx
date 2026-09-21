import ReceptionMain from "../../components/pages/reception/ReceptionMain.jsx";
import { usePageTitle } from "../../hooks/usePageTitle.js";

function Reception() {
  usePageTitle("Reception");

  return <ReceptionMain />;
}

export default Reception;
