import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./CandidateDashboard.css";

const APPLICATION_STAGES = [
  "APPLIED",
  "SCREENING",
  "SHORTLISTED",
  "INTERVIEW",
  "OFFER",
  "HIRED",
];

const getStageIndex = (status) => {
  return APPLICATION_STAGES.indexOf(status);
};

const formatStatus = (status) => {
  if (!status) {
    return "";
  }

  return status
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
};

const formatDate = (value) => {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleDateString(
    undefined,
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    }
  );
};

const formatDateTime = (value) => {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleString(
    undefined,
    {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }
  );
};

function CandidateDashboard() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [applications, setApplications] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [resumes, setResumes] = useState([]);

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [profileForm, setProfileForm] = useState({
    phone: "",
    location: "",
    bio: "",
    experience: "",
    education: "",
  });

  const loadDashboard = async () => {
    try {
      setLoading(true);

      const [
        profileResponse,
        applicationsResponse,
        jobsResponse,
        resumesResponse,
      ] = await Promise.all([
        API.get("/candidate/profile"),
        API.get("/candidate/applications"),
        API.get("/jobs/"),
        API.get("/my-resumes"),
      ]);

      const candidateProfile =
        profileResponse.data;

      setProfile(candidateProfile);

      setProfileForm({
        phone: candidateProfile.phone || "",
        location: candidateProfile.location || "",
        bio: candidateProfile.bio || "",
        experience:
          candidateProfile.experience || "",
        education:
          candidateProfile.education || "",
      });

      setApplications(
        applicationsResponse.data.applications || []
      );

      setJobs(jobsResponse.data || []);

      setResumes(
        resumesResponse.data.resumes || []
      );

      setError("");
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
          "Unable to load candidate dashboard."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const user = JSON.parse(
      localStorage.getItem("user") || "null"
    );

    if (!user || user.role !== "JOB_SEEKER") {
      navigate("/login");
      return;
    }

    loadDashboard();
  }, [navigate]);

  const handleProfileChange = (event) => {
    const { name, value } = event.target;

    setProfileForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const saveProfile = async (event) => {
    event.preventDefault();

    try {
      setSavingProfile(true);
      setMessage("");
      setError("");

      await API.put(
        "/candidate/profile",
        profileForm
      );

      setMessage(
        "Profile updated successfully."
      );

      await loadDashboard();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to update profile."
      );
    } finally {
      setSavingProfile(false);
    }
  };

  const uploadResume = async () => {
    if (!selectedFile) {
      setError("Please select a resume first.");
      return;
    }

    try {
      setUploading(true);
      setMessage("");
      setError("");

      const formData = new FormData();

      formData.append(
        "file",
        selectedFile
      );

      await API.post(
        "/upload-resume",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setSelectedFile(null);

      const fileInput =
        document.getElementById(
          "candidate-resume-upload"
        );

      if (fileInput) {
        fileInput.value = "";
      }

      setMessage(
        "Resume uploaded and parsed successfully."
      );

      await loadDashboard();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to upload resume."
      );
    } finally {
      setUploading(false);
    }
  };

  const getApplicationHistory = (
    application
  ) => {
    return Array.isArray(
      application.status_history
    )
      ? application.status_history
      : [];
  };

  if (loading) {
    return (
      <div className="candidate-dashboard">
        <div className="candidate-loading">
          Loading your dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="candidate-dashboard">
      <div className="candidate-dashboard-header">
        <div>
          <p className="candidate-eyebrow">
            Candidate workspace
          </p>

          <h1>
            Welcome, {profile?.name || "Candidate"}
          </h1>

          <p>
            Manage your profile, resume and track your
            applications.
          </p>
        </div>

        <button
          className="candidate-browse-button"
          onClick={() => navigate("/jobs")}
        >
          Browse Jobs
        </button>
      </div>

      {message && (
        <div className="candidate-success-message">
          {message}
        </div>
      )}

      {error && (
        <div className="candidate-error-message">
          {error}
        </div>
      )}

      <div className="candidate-dashboard-grid">
        <section className="candidate-card">
          <div className="candidate-card-header">
            <div>
              <p className="candidate-card-label">
                Profile
              </p>
              <h2>Your Information</h2>
            </div>
          </div>

          <form onSubmit={saveProfile}>
            <div className="candidate-form-grid">
              <div>
                <label>Phone</label>
                <input
                  name="phone"
                  value={profileForm.phone}
                  onChange={handleProfileChange}
                  placeholder="Phone number"
                />
              </div>

              <div>
                <label>Location</label>
                <input
                  name="location"
                  value={profileForm.location}
                  onChange={handleProfileChange}
                  placeholder="City, Country"
                />
              </div>
            </div>

            <div>
              <label>Bio</label>
              <textarea
                name="bio"
                value={profileForm.bio}
                onChange={handleProfileChange}
                placeholder="Tell employers about yourself"
              />
            </div>

            <div>
              <label>Experience</label>
              <textarea
                name="experience"
                value={profileForm.experience}
                onChange={handleProfileChange}
                placeholder="Describe your experience"
              />
            </div>

            <div>
              <label>Education</label>
              <textarea
                name="education"
                value={profileForm.education}
                onChange={handleProfileChange}
                placeholder="Your education"
              />
            </div>

            <button
              type="submit"
              className="candidate-primary-button"
              disabled={savingProfile}
            >
              {savingProfile
                ? "Saving..."
                : "Save Profile"}
            </button>
          </form>
        </section>

        <section className="candidate-card">
          <div className="candidate-card-header">
            <div>
              <p className="candidate-card-label">
                Resume intelligence
              </p>

              <h2>Resume</h2>
            </div>
          </div>

          <div className="resume-upload-box">
            <input
              id="candidate-resume-upload"
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(event) =>
                setSelectedFile(
                  event.target.files?.[0] || null
                )
              }
            />

            <button
              className="candidate-primary-button"
              onClick={uploadResume}
              disabled={uploading}
            >
              {uploading
                ? "Uploading..."
                : "Upload Resume"}
            </button>
          </div>

          <div className="resume-list">
            <h3>Your uploaded resumes</h3>

            {resumes.length === 0 ? (
              <p className="muted-text">
                No resumes uploaded yet.
              </p>
            ) : (
              resumes.map((resume) => (
                <div
                  className="resume-item"
                  key={resume.id}
                >
                  <div>
                    <strong>
                      {resume.original_filename}
                    </strong>

                    <span>
                      {resume.status || "Uploaded"}
                    </span>
                  </div>

                  <small>
                    {resume.uploaded_at
                      ? formatDate(
                          resume.uploaded_at
                        )
                      : ""}
                  </small>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <section className="candidate-card applications-section">
        <div className="candidate-card-header">
          <div>
            <p className="candidate-card-label">
              Hiring progress
            </p>

            <h2>My Applications</h2>

            <p>
              Follow each application and review feedback
              from the hiring team.
            </p>
          </div>

          <span className="application-count">
            {applications.length} application
            {applications.length !== 1 ? "s" : ""}
          </span>
        </div>

        {applications.length === 0 ? (
          <div className="empty-applications">
            <h3>No applications yet</h3>

            <p>
              Browse available jobs and submit your first
              application.
            </p>

            <button
              className="candidate-primary-button"
              onClick={() => navigate("/jobs")}
            >
              Browse Jobs
            </button>
          </div>
        ) : (
          <div className="candidate-application-list">
            {applications.map((application) => {
              const status =
                application.status || "APPLIED";

              const stageIndex =
                getStageIndex(status);

              const history =
                getApplicationHistory(
                  application
                );

              const isRejected =
                status === "REJECTED";

              return (
                <article
                  className="candidate-application-card"
                  key={application.id}
                >
                  <div className="candidate-application-header">
                    <div>
                      <span className="candidate-application-label">
                        Application
                      </span>

                      <h3>
                        {application.job_title}
                      </h3>

                      <p>
                        {application.company_name}
                        {application.location
                          ? ` • ${application.location}`
                          : ""}
                      </p>
                    </div>

                    <div className="candidate-application-fit">
                      <span>AI Fit</span>

                      <strong>
                        {application.match_score !== null &&
                        application.match_score !==
                          undefined
                          ? `${application.match_score}%`
                          : "Not calculated"}
                      </strong>
                    </div>
                  </div>

                  <div className="candidate-application-meta">
                    <span>
                      Applied{" "}
                      {formatDate(
                        application.applied_at
                      )}
                    </span>

                    <span
                      className={`candidate-status ${
                        isRejected
                          ? "rejected"
                          : ""
                      }`}
                    >
                      {formatStatus(status)}
                    </span>
                  </div>

                  {!isRejected && (
                    <div className="application-timeline">
                      {APPLICATION_STAGES.map(
                        (stage, index) => {
                          const completed =
                            stageIndex >= index;

                          const current =
                            stage === status;

                          return (
                            <div
                              className={`timeline-stage ${
                                completed
                                  ? "completed"
                                  : ""
                              } ${
                                current
                                  ? "current"
                                  : ""
                              }`}
                              key={stage}
                            >
                              <div className="timeline-marker">
                                {completed
                                  ? "✓"
                                  : ""}
                              </div>

                              <span>
                                {formatStatus(
                                  stage
                                )}
                              </span>
                            </div>
                          );
                        }
                      )}
                    </div>
                  )}

                  {isRejected && (
                    <div className="application-rejected">
                      <strong>
                        Application closed
                      </strong>

                      <p>
                        This application is no longer
                        progressing through the hiring
                        pipeline.
                      </p>
                    </div>
                  )}

                  <div className="current-application-status">
                    <span>
                      Current status
                    </span>

                    <strong>
                      {formatStatus(status)}
                    </strong>
                  </div>

                  {history.length > 0 && (
                    <div className="application-history">
                      <div className="history-heading">
                        <div>
                          <span>
                            Application history
                          </span>

                          <strong>
                            {history.length} update
                            {history.length !== 1
                              ? "s"
                              : ""}
                          </strong>
                        </div>
                      </div>

                      <div className="history-list">
                        {history.map(
                          (event) => (
                            <div
                              className="history-item"
                              key={event.id}
                            >
                              <div className="history-dot" />

                              <div className="history-content">
                                <div className="history-title-row">
                                  <strong>
                                    {formatStatus(
                                      event.new_status
                                    )}
                                  </strong>

                                  <span>
                                    {formatDateTime(
                                      event.changed_at
                                    )}
                                  </span>
                                </div>

                                {event.changed_by && (
                                  <small>
                                    Updated by{" "}
                                    {
                                      event.changed_by
                                    }
                                  </small>
                                )}

                                {event.feedback && (
                                  <div className="history-feedback">
                                    <span>
                                      Employer feedback
                                    </span>

                                    <p>
                                      {
                                        event.feedback
                                      }
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  )}

                  <div className="candidate-application-actions">
                    <button
                      className="secondary-application-button"
                      onClick={() =>
                        navigate(
                          `/jobs/${application.job_id}`
                        )
                      }
                    >
                      View Job
                    </button>

                    <button
                      className="primary-application-button"
                      onClick={() =>
                        navigate(
                          `/career-fit?job=${application.job_id}`
                        )
                      }
                    >
                      View Career Fit
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="candidate-card">
        <div className="candidate-card-header">
          <div>
            <p className="candidate-card-label">
              Opportunities
            </p>

            <h2>Available Jobs</h2>
          </div>
        </div>

        <div className="candidate-job-grid">
          {jobs.slice(0, 6).map((job) => (
            <div
              className="candidate-job-card"
              key={job.id}
            >
              <h3>{job.title}</h3>

              <p>
                {job.company_name ||
                  job.company?.name ||
                  "Company"}
              </p>

              <span>
                {job.location || "Location not specified"}
              </span>

              <button
                className="candidate-secondary-button"
                onClick={() =>
                  navigate(`/jobs/${job.id}`)
                }
              >
                View Job
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default CandidateDashboard;
