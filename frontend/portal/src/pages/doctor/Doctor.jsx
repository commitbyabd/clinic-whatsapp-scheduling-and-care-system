import DoctorMain from "../../components/pages/doctor/DoctorMain.jsx";
import { usePageTitle } from "../../hooks/usePageTitle.js";

function Doctor() {
  usePageTitle("Doctor");

  return <DoctorMain />;
}

export default Doctor;
