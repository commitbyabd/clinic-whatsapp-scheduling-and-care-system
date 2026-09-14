import Careers from "./careers/Careers";
import Details from "./details/Details";
import ContactHeader from "./header/ContactHeader";
import Whatsapp from "./whatsapp/Whatsapp";

function ContactUsMain() {
  return (
    <>
      <ContactHeader />
      <Whatsapp />
      <Details />
      {/* "See all openings" on Our Team lands here — recruitment is kept
          separate from the patient enquiry form above. */}
      <Careers />
    </>
  );
}

export default ContactUsMain;
