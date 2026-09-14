import DashboardMain from "../../components/pages/dashboard/DashboardMain.jsx";
import { usePageTitle } from "../../hooks/usePageTitle.js";

function Dashboard() {
  usePageTitle("Staff");

  return <DashboardMain />;
}

export default Dashboard;
