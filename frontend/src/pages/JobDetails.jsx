import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../services/api";
import "./JobDetails.css";

function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState(null);

  const [application, setApplication] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loadingCandidateData, setLoadingCandidateData] =
    useState(false);
  const [applying, setApplying] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // ============================================================
  // LOAD JOB
  // ============================================================

  useEffect(() => {
    const loadJob = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await API.get(`/jobs/${id}`);

        setJob(response.data);
      } catch (err) {
        console.error(err);

        setError(
          err.response?.data?.detail ||
            "Unable to load job."
        );
      } finally {
        setLoading(false);
      }
    };

    loadJob();
  }, [id]);

  // ============================================================
  // LOAD CANDIDATE DATA
  // ============================================================

  useEffect(() => {
    const loadCandidateData = async () => {
      const token = localStorage.getItem("token");

      const user = JSON.parse(
        localStorage.getItem("user") || "null"
      );

      if (
        !token ||
        !user ||
        user.role !== "JOB_SEEKER"
      ) {
        return;
      }

      try {
        setLoadingCandidateData(true);

        const [
          resumesResponse,
          applicationsResponse,
        ] = await Promise.all([
          API.get("/my-resumes"),
          API.get("/candidate/applications"),
        ]);

        const resumeList = Array.isArray(resumesResponse.data)
          ? resumesResponse.data
          : (resumesResponse.data.resumes || []);

        const applicationList =
          applicationsResponse.data.applications || [];

        setResumes(resumeList);

        // --------------------------------------------------------
        // Select latest resume automatically
        // --------------------------------------------------------

        if (resumeList.length > 0) {
          setSelectedResume(
            resumeList[resumeList.length - 1].id
          );
        }

        // --------------------------------------------------------
        // Find whether candidate already applied
        // --------------------------------------------------------

        const existingApplication =
          applicationList.find((item) => {
            if (
              item.job_id !== undefined &&
              item.job_id !== null
            ) {
              return (
                Number(item.job_id) ===
                Number(id)
              );
            }

            if (
              item.job_title &&
              job?.title
            ) {
              return (
                item.job_title ===
                job.title
              );
            }

            return false;
          });

        if (existingApplication) {
          setApplication(
            existingApplication
          );
        }

      } catch (err) {
        console.error(
          "Unable to load candidate data:",
          err
        );
      } finally {
        setLoadingCandidateData(false);
      }
    };

    if (job) {
      loadCandidateData();
    }
  }, [id, job]);

  // ============================================================
  // APPLY FOR JOB
  // ============================================================

  const applyForJob = async () => {
    const token = localStorage.getItem("token");

    const user = JSON.parse(
      localStorage.getItem("user") || "null"
    );

    setMessage("");
    setError("");

    if (!token || !user) {
      navigate("/login");
      return;
    }

    if (user.role !== "JOB_SEEKER") {
      setError(
        "Only job seekers can apply for jobs."
      );
      return;
    }

    if (application) {
      setMessage(
        "You have already applied for this job."
      );
      return;
    }

    if (resumes.length === 0) {
      setError(
        "Please upload a resume from your Candidate Dashboard before applying."
      );
      return;
    }

    if (!selectedResume) {
      setError(
        "Please select a resume before applying."
      );
      return;
    }

    try {
      setApplying(true);

      const response = await API.post(
        "/candidate/apply",
        {
          job_id: Number(id),
          resume_id: Number(selectedResume),
        }
      );

      setMessage(
        response.data?.message ||
          "Application submitted successfully."
      );

      // --------------------------------------------------------
      // Immediately update the page to "Applied"
      // --------------------------------------------------------

      setApplication({
        job_id: Number(id),
        job_title: job.title,
        status: "APPLIED",
        match_score: null,
        applied_at: new Date().toISOString(),
      });

    } catch (err) {
      console.error(
        "Application error:",
        err
      );

      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        navigate("/login", {
          replace: true,
        });

        return;
      }

      // --------------------------------------------------------
      // Backend may tell us the application already exists
      // --------------------------------------------------------

      const backendMessage =
        err.response?.data?.detail ||
        "";

      if (
        backendMessage
          .toLowerCase()
          .includes("already")
      ) {
        setApplication({
          job_id: Number(id),
          job_title: job.title,
          status: "APPLIED",
        });

        setMessage(
          "You have already applied for this job."
        );

        return;
      }

      setError(
        backendMessage ||
          "Unable to submit application."
      );
    } finally {
      setApplying(false);
    }
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <div className="job-details-loading">
        Loading job...
      </div>
    );
  }

  // ============================================================
  // JOB NOT FOUND
  // ============================================================

  if (!job) {
    return (
      <div className="job-details-loading">
        {error || "Job not found"}
      </div>
    );
  }

  const skills = Array.isArray(job.skills)
    ? job.skills
    : [];

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div className="job-details-page">

      <div className="job-details-card">

        {/* ==================================================
            HEADER
            ================================================== */}

        <div className="job-details-header">

          <div>

            <span className="job-company">
              {job.company_name}
            </span>

            <h1>
              {job.title}
            </h1>

            <p className="job-location">
              📍{" "}
              {job.location ||
                "Location not specified"}
            </p>

          </div>

        </div>

        {/* ==================================================
            MESSAGES
            ================================================== */}

        {message && (
          <div className="job-success">
            {message}
          </div>
        )}

        {error && (
          <div className="job-error">
            {error}
          </div>
        )}

        {/* ==================================================
            JOB INFORMATION
            ================================================== */}

        <div className="job-info-row">

          {job.salary && (
            <div>
              <span>
                Salary
              </span>

              <strong>
                {job.salary}
              </strong>
            </div>
          )}

          {job.experience && (
            <div>
              <span>
                Experience
              </span>

              <strong>
                {job.experience}
              </strong>
            </div>
          )}

          {job.employment_type && (
            <div>
              <span>
                Employment
              </span>

              <strong>
                {job.employment_type}
              </strong>
            </div>
          )}

        </div>

        {/* ==================================================
            DESCRIPTION
            ================================================== */}

        <section className="job-description-section">

          <h2>
            About the role
          </h2>

          <p>
            {job.description}
          </p>

        </section>

        {/* ==================================================
            SKILLS
            ================================================== */}

        <section>

          <h2>
            Required skills
          </h2>

          <div className="job-skill-tags">

            {skills.length > 0 ? (
              skills.map((skill) => (
                <span key={skill}>
                  {skill}
                </span>
              ))
            ) : (
              <span>
                Skills not specified
              </span>
            )}

          </div>

        </section>

        {/* ==================================================
            APPLICATION
            ================================================== */}

        <section className="job-application-section">

          <h2>
            {application
              ? "Application Submitted"
              : "Apply for this position"}
          </h2>

          {application ? (

            <div className="job-already-applied">

              <div>
                <strong>
                  ✓ You have already applied
                </strong>

                <p>
                  Application status:
                  {" "}
                  <strong>
                    {application.status ||
                      "APPLIED"}
                  </strong>
                </p>

                {application.match_score !==
                  null &&
                  application.match_score !==
                    undefined && (
                    <p>
                      Career Fit:
                      {" "}
                      {application.match_score}%
                    </p>
                  )}

              </div>

              <button
                className="career-fit-button"
                onClick={() =>
                  navigate(
                    `/career-fit?job=${job.id}`
                  )
                }
              >
                View Career Fit →
              </button>

            </div>

          ) : loadingCandidateData ? (

            <p>
              Preparing application...
            </p>

          ) : resumes.length === 0 ? (

            <div className="job-resume-warning">

              <p>
                You haven't uploaded a resume yet.
              </p>

              <button
                className="career-fit-button"
                onClick={() =>
                  navigate(
                    "/candidate-dashboard"
                  )
                }
              >
                Go to Candidate Dashboard
              </button>

            </div>

          ) : (

            <div className="job-resume-selection">

              <p>
                Select the resume you want the
                employer to review with your
                application.
              </p>

              <label>
                Select Resume
              </label>

              <select
                value={
                  selectedResume || ""
                }
                onChange={(event) =>
                  setSelectedResume(
                    Number(
                      event.target.value
                    )
                  )
                }
              >

                <option value="">
                  Select a resume
                </option>

                {resumes.map((resume) => (
                  <option
                    key={resume.id}
                    value={resume.id}
                  >
                    {resume.filename} —{" "}
                    {resume.status}
                  </option>
                ))}

              </select>

              <button
                className="apply-button"
                onClick={applyForJob}
                disabled={
                  applying ||
                  !selectedResume
                }
              >
                {applying
                  ? "Applying..."
                  : "Apply Now"}
              </button>

            </div>

          )}

        </section>

        {/* ==================================================
            CAREER FIT
            ================================================== */}

        <button
          className="career-fit-button"
          onClick={() =>
            navigate(
              `/career-fit?job=${job.id}`
            )
          }
        >
          Check Your Career Fit →
        </button>

      </div>

    </div>
  );
}

export default JobDetails;
