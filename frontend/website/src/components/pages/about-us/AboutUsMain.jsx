import Facilities from "./facilities/Facilities";
import Fund from "./fund/Fund";
import Mission from "./mission/Mission";
import PatientsStat from "./patients-stat/PatientsStat";

function AboutUsMain() {
  return (
    <>
      <Mission />
      <PatientsStat />
      <Facilities />
      <Fund />
    </>
  );
}

export default AboutUsMain;
