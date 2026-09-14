import { BrowserRouter } from "react-router-dom";
import AuthProvider from "./context/AuthProvider.jsx";
import ProjectRoutes from "./routes/ProjectRoutes.jsx";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProjectRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
