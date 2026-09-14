import CarePathway from "./care-pathway/CarePathway";
import ClinicDays from "./clinic-days/ClinicDays";
import Doctors from "./doctors/Doctors";
import TeamHeader from "./header/TeamHeader";
import Hiring from "./hiring/Hiring";
import Nurses from "./nurses/Nurses";

function OurTeamMain() {
  return (
    <>
      <TeamHeader />
      <Doctors />
      {/* Sits between the two photographic sections so they do not run
          back to back. */}
      <CarePathway />
      <Nurses />
      <ClinicDays />
      <Hiring />
    </>
  );
}

export default OurTeamMain;
