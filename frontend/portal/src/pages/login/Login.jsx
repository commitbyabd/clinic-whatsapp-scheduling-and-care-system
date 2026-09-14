import LoginMain from "../../components/pages/login/LoginMain.jsx";
import { usePageTitle } from "../../hooks/usePageTitle.js";

function Login() {
  usePageTitle("Sign in");

  return <LoginMain />;
}

export default Login;
