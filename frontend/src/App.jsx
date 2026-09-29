import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import HiringPipeline from "./pages/HiringPipeline";
import Sidebar from "./components/Sidebar";
import ProtectedRoute from "./components/protectedroute";

import Home from "./pages/Home";
import Login from "./pages/login";
import CandidateRegister from "./pages/CandidateRegister";

import BrowseJobs from "./pages/BrowseJobs";
import JobDetails from "./pages/JobDetails";

import EmployerDashboard from "./pages/EmployerDashboard";
import EmployerApplicants from "./pages/EmployerApplicants";
import EmployerApplicantDetails from "./pages/EmployerApplicantDetails";

import CandidateDashboard from "./pages/CandidateDashboard";
import CareerFit from "./pages/CareerFit";
import SkillGap from "./pages/SkillGap";

import Dashboard from "./pages/Dashboard";
import UploadResume from "./pages/uploadResume";
import UploadJob from "./pages/uploadjob";
import Candidates from "./pages/candidates";
import Ranking from "./pages/Ranking";
import CandidateDetails from "./pages/candidatedetails";


import AdminDashboard from "./pages/AdminDashboard";
import Notifications from "./pages/Notifications";
function Layout() {
  const location = useLocation();

  const path = location.pathname;

  const publicPage =
    path === "/" ||
    path === "/login" ||
    path === "/register" ||
    path === "/companies" ||
    path === "/career-fit" ||
    path === "/employer" ||
    path === "/employer/applicants" ||
    path.startsWith("/employer/applicants/") ||
    path === "/candidate-dashboard" ||
    path === "/jobs" ||
    path === "/employer/pipeline" ||
    path.startsWith("/jobs/");

  const showSidebar = !publicPage;

  return (
    <div className="app-layout">

      {showSidebar && <Sidebar />}

      <main
        className={
          showSidebar
            ? "main-content"
            : "full-content"
        }
      >

        <Routes>

          <Route
            path="/"
            element={<Home />}
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/register"
            element={<CandidateRegister />}
          />

          <Route
            path="/jobs"
            element={<BrowseJobs />}
          />

          <Route
            path="/jobs/:id"
            element={<JobDetails />}
          />

          <Route
            path="/companies"
            element={
              <div style={{ padding: "40px" }}>
                Companies page coming soon.
              </div>
            }
          />

          <Route
            path="/career-fit"
            element={<CareerFit />}
          />

          <Route
            path="/skill-gap/:jobId"
            element={
              <ProtectedRoute>
                <SkillGap />
              </ProtectedRoute>
            }
          />

          <Route
            path="/employer"
            element={<EmployerDashboard />}
          />

          <Route
            path="/employer/applicants"
            element={<EmployerApplicants />}
          />
<Route
  path="/employer/pipeline"
  element={<HiringPipeline />}
/>

          <Route
            path="/employer/applicants/:id"
            element={<EmployerApplicantDetails />}
          />

          <Route
            path="/candidate-dashboard"
            element={<CandidateDashboard />}
          />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
            <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <Notifications />
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

      </main>

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
