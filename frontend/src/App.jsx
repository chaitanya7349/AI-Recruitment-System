import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";

import Sidebar from "./components/Sidebar";
import ProtectedRoute from "./components/protectedroute";

import Home from "./pages/Home";
import Login from "./pages/login";
import BrowseJobs from "./pages/BrowseJobs";
import Dashboard from "./pages/Dashboard";
import UploadResume from "./pages/uploadResume";
import UploadJob from "./pages/uploadjob";
import Candidates from "./pages/candidates";
import Ranking from "./pages/Ranking";
import CandidateDetails from "./pages/candidatedetails";
import JobDetails from "./pages/JobDetails";
function Layout() {
  const location = useLocation();

  const publicPages = [
    "/",
    "/login",
    "/register",
    "/jobs",
    "/companies",
    "/career-fit",
    "/employer",
  ];

  const showSidebar = !publicPages.includes(location.pathname);

  return (
    <div style={{ display: "flex" }}>

      {showSidebar && <Sidebar />}

      <div
        style={{
          marginLeft: showSidebar ? "250px" : "0",
          width: "100%",
          minHeight: "100vh",
        }}
      >

        <Routes>

  {/* ================= PUBLIC ================= */}

  <Route path="/" element={<Home />} />

  <Route
    path="/login"
    element={<Login />}
  />

  <Route
    path="/register"
    element={
      <div style={{ padding: "50px" }}>
        Registration page coming next.
      </div>
    }
  />

  {/* Browse Jobs */}
  <Route
    path="/jobs"
    element={<BrowseJobs />}
  />

  {/* Job Details */}
  <Route
    path="/jobs/:id"
    element={<JobDetails />}
  />

  <Route
    path="/companies"
    element={
      <div style={{ padding: "50px" }}>
        Companies page coming next.
      </div>
    }
  />

  <Route
    path="/career-fit"
    element={
      <div style={{ padding: "50px" }}>
        Career Intelligence page coming next.
      </div>
    }
  />

  <Route
    path="/employer"
    element={
      <div style={{ padding: "50px" }}>
        Employer platform coming next.
      </div>
    }
  />

  {/* ================= PROTECTED ================= */}

  <Route
    path="/dashboard"
    element={
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    }
  />

  <Route
    path="/upload-resume"
    element={
      <ProtectedRoute>
        <UploadResume />
      </ProtectedRoute>
    }
  />

  <Route
    path="/upload-job"
    element={
      <ProtectedRoute>
        <UploadJob />
      </ProtectedRoute>
    }
  />

  <Route
    path="/candidates"
    element={
      <ProtectedRoute>
        <Candidates />
      </ProtectedRoute>
    }
  />

  <Route
    path="/ranking"
    element={
      <ProtectedRoute>
        <Ranking />
      </ProtectedRoute>
    }
  />

  <Route
    path="/candidate/:id"
    element={
      <ProtectedRoute>
        <CandidateDetails />
      </ProtectedRoute>
    }
  />

</Routes>

      </div>

    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}

export default App;
