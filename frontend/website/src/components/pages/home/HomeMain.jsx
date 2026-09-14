import ClosingCta from "./closing-cta/ClosingCta";
import FundTeaser from "./fund-teaser/FundTeaser";
import Hero from "./hero/Hero";
import Pricing from "./pricing/Pricing";
import Stats from "./stats/Stats";
import StatusBoard from "./status-board/StatusBoard";
import SymptomRouter from "./symptom-router/SymptomRouter";
import WhoWeAre from "./who-we-are/WhoWeAre";

function HomeMain() {
  return (
    <>
      <Hero />
      <WhoWeAre />
      <Stats />
      {/* How long will I wait, who do I need, what will it cost — the three
          questions that stop people booking, answered before the Fund
          teaser rather than after it. */}
      <StatusBoard />
      <SymptomRouter />
      <Pricing />
      <FundTeaser />
      <ClosingCta />
    </>
  );
}

export default HomeMain;
