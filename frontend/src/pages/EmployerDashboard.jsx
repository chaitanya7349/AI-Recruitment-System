import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./EmployerDashboard.css";
import HiringPipeline from "./HiringPipeline";

function EmployerDashboard() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [editingJob, setEditingJob] = useState(null);

  const [form, setForm] = useState({
    title: "",
    description: "",
    location: "",
    salary: "",
    experience: "",
    employment_type: "Full-time",
    skills: "",
  });

  const currentUser = JSON.parse(
    localStorage.getItem("user") || "null"
  );

  // ============================================================
  // LOAD EMPLOYER DASHBOARD
  // ============================================================

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await API.get("/employer/dashboard");

      setDashboard(response.data);
    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        setError(
          "Your session has expired. Please login again."
        );
      } else {
        setError(
          err.response?.data?.detail ||
            "Unable to load employer dashboard."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // AUTHENTICATION CHECK
  // ============================================================

  useEffect(() => {
    const user = JSON.parse(
      localStorage.getItem("user") || "null"
    );

    const token = localStorage.getItem("token");

    if (!token || !user) {
      navigate("/login");
      return;
    }

    if (user.role !== "EMPLOYER_USER") {
      navigate("/dashboard");
      return;
    }

    loadDashboard();
  }, []);

  // ============================================================
  // FORM HANDLING
  // ============================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setForm({
      title: "",
      description: "",
      location: "",
      salary: "",
      experience: "",
      employment_type: "Full-time",
      skills: "",
    });

    setEditingJob(null);
    setShowForm(false);
  };

  const openCreateForm = () => {
    setMessage("");
    setError("");
    setEditingJob(null);

    setForm({
      title: "",
      description: "",
      location: "",
      salary: "",
      experience: "",
      employment_type: "Full-time",
      skills: "",
    });

    setShowForm(true);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const openEditForm = (job) => {
    setMessage("");
    setError("");
    setEditingJob(job);

    setForm({
      title: job.title || "",
      description: job.description || "",
      location: job.location || "",
      salary: job.salary || "",
      experience: job.experience || "",
      employment_type:
        job.employment_type || "Full-time",
      skills: Array.isArray(job.skills)
        ? job.skills.join(", ")
        : "",
    });

    setShowForm(true);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ============================================================
  // CREATE / UPDATE JOB
  // ============================================================

  const saveJob = async (event) => {
    event.preventDefault();

    setMessage("");
    setError("");

    const skills = form.skills
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean);

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      location: form.location.trim(),
      salary: form.salary.trim(),
      experience: form.experience.trim(),
      employment_type: form.employment_type,
      skills,
    };

    try {
      if (editingJob) {
        await API.put(
          `/jobs/${editingJob.id}`,
          payload
        );

        setMessage("Job updated successfully.");
      } else {
        await API.post("/jobs/", payload);

        setMessage("Job posted successfully.");
      }

      resetForm();
      await loadDashboard();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to save job."
      );
    }
  };

  // ============================================================
  // CLOSE JOB
  // ============================================================

  const closeJob = async (jobId) => {
    const confirmed = window.confirm(
      "Are you sure you want to close this job?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await API.patch(
        `/jobs/${jobId}/close`
      );

      setMessage("Job closed successfully.");

      await loadDashboard();
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Unable to close job."
      );
    }
  };

  // ============================================================
  // LOGOUT
  // ============================================================

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    navigate("/login");
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <div className="employer-loading">
        Loading employer dashboard...
      </div>
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

  if (error && !dashboard) {
    return (
      <div className="employer-error-page">
        <h2>Unable to load dashboard</h2>

        <p>{error}</p>

        <button onClick={() => navigate("/login")}>
          Go to Login
        </button>
      </div>
    );
  }

  // ============================================================
  // SAFE VALUES
  // ============================================================

  const company = dashboard?.company || {};

  const statistics = dashboard?.statistics || {};

  const jobs = Array.isArray(dashboard?.jobs)
    ? dashboard.jobs
    : [];

  const totalJobs = statistics.total_jobs ?? jobs.length;

  const activeJobs =
    statistics.active_jobs ??
    jobs.filter(
      (job) => job.status === "ACTIVE"
    ).length;

  const totalApplications =
    statistics.total_applications ?? 0;

  const employerName =
    dashboard?.employer?.name ||
    currentUser?.name ||
    "Employer";

  const employerEmail =
    dashboard?.employer?.email ||
    currentUser?.email ||
    "";

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <div className="employer-page">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="employer-header">

        <div>
          <span className="employer-eyebrow">
            EMPLOYER PLATFORM
          </span>

          <h1>
            Employer Dashboard
          </h1>

          <p>
            Manage your company, jobs and hiring activity.
          </p>
        </div>

        <div className="employer-header-actions">

          <button
            className="applicants-button"
            onClick={() =>
              navigate("/employer/applicants")
            }
          >
            View Applicants
          </button>

          <button
            className="logout-button"
            onClick={logout}
          >
            Logout
          </button>

        </div>

      </header>

      {/* ======================================================
          MESSAGES
      ====================================================== */}

      {message && (
        <div className="success-message">
          {message}
        </div>
      )}

      {error && dashboard && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* ======================================================
          COMPANY
      ====================================================== */}

      <section className="company-card">

        <div className="company-main">

          <div className="company-logo">
            {company.name
              ? company.name.charAt(0).toUpperCase()
              : "C"}
          </div>

          <div>

            <h2>
              {company.name || "Company"}
            </h2>

            <p>
              {company.description ||
                "Company profile"}
            </p>

            <div className="company-meta">

              <span>
                📍{" "}
                {company.location ||
                  "Location not specified"}
              </span>

              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noreferrer"
                >
                  🌐 Website
                </a>
              )}

            </div>

          </div>

        </div>

        <div className="employer-person">

          <strong>
            {employerName}
          </strong>

          <span>
            {dashboard?.employer?.designation ||
              dashboard?.employer?.role_in_company ||
              "Employer"}
          </span>

          {employerEmail && (
            <small>
              {employerEmail}
            </small>
          )}

        </div>

      </section>

      {/* ======================================================
          STATISTICS
      ====================================================== */}

      <section className="stats-grid">

        <div className="stat-card">
          <span>Total Jobs</span>

          <strong>
            {totalJobs}
          </strong>
        </div>

        <div className="stat-card">
          <span>Active Jobs</span>

          <strong>
            {activeJobs}
          </strong>
        </div>

        <div className="stat-card">
          <span>Applications</span>

          <strong>
            {totalApplications}
          </strong>
        </div>

      </section>

      {/* ======================================================
          QUICK ACTIONS
      ====================================================== */}

      <section className="quick-actions">

        <div className="quick-action-card">

          <div>
            <span className="section-label">
              TALENT
            </span>

            <h3>
              Review Applicants
            </h3>

            <p>
              View candidates who have applied
              to your jobs and manage their
              hiring stages.
            </p>
          </div>

          <button
            className="primary-job-button"
            onClick={() =>
              navigate("/employer/applicants")
            }
          >
            View Applicants
          </button>

        </div>

        <div className="quick-action-card">

          <div>
            <span className="section-label">
              HIRING
            </span>

            <h3>
              Create a Job
            </h3>

            <p>
              Publish a new opportunity and
              start receiving candidates.
            </p>
          </div>

          <button
            className="primary-job-button"
            onClick={openCreateForm}
          >
            + Post New Job
          </button>

        </div>

      </section>

      {/* ======================================================
          JOB FORM
      ====================================================== */}

      {showForm && (
        <section className="job-form-card">

          <div className="section-heading">

            <div>

              <span className="section-label">
                JOB MANAGEMENT
              </span>

              <h2>
                {editingJob
                  ? "Edit Job"
                  : "Post a New Job"}
              </h2>

            </div>

            <button
              className="cancel-button"
              onClick={resetForm}
              type="button"
            >
              Cancel
            </button>

          </div>

          <form onSubmit={saveJob}>

            <div className="form-grid">

              <div className="form-group full">

                <label>
                  Job Title
                </label>

                <input
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="Python Backend Developer"
                  required
                />

              </div>

              <div className="form-group">

                <label>
                  Location
                </label>

                <input
                  name="location"
                  value={form.location}
                  onChange={handleChange}
                  placeholder="Bengaluru, India"
                />

              </div>

              <div className="form-group">

                <label>
                  Salary
                </label>

                <input
                  name="salary"
                  value={form.salary}
                  onChange={handleChange}
                  placeholder="₹6,00,000 - ₹10,00,000"
                />

              </div>

              <div className="form-group">

                <label>
                  Experience
                </label>

                <input
                  name="experience"
                  value={form.experience}
                  onChange={handleChange}
                  placeholder="1-3 years"
                />

              </div>

              <div className="form-group">

                <label>
                  Employment Type
                </label>

                <select
                  name="employment_type"
                  value={form.employment_type}
                  onChange={handleChange}
                >
                  <option>Full-time</option>
                  <option>Part-time</option>
                  <option>Contract</option>
                  <option>Internship</option>
                  <option>Remote</option>
                </select>

              </div>

              <div className="form-group full">

                <label>
                  Required Skills
                </label>

                <input
                  name="skills"
                  value={form.skills}
                  onChange={handleChange}
                  placeholder="Python, FastAPI, PostgreSQL, REST API, Git"
                />

                <small>
                  Separate skills using commas.
                </small>

              </div>

              <div className="form-group full">

                <label>
                  Job Description
                </label>

                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Describe the role, responsibilities and requirements..."
                  rows="7"
                  required
                />

              </div>

            </div>

            <button
              type="submit"
              className="primary-job-button"
            >
              {editingJob
                ? "Update Job"
                : "Publish Job"}
            </button>

          </form>

        </section>
      )}

      {/* ======================================================
          HIRING PIPELINE
      ====================================================== */}

      <section className="embedded-pipeline-section">
        <HiringPipeline />
      </section>

      {/* ======================================================
          MY JOBS
      ====================================================== */}

      <section className="jobs-section">

        <div className="section-heading">

          <div>

            <span className="section-label">
              HIRING
            </span>

            <h2>
              My Jobs
            </h2>

          </div>

          {!showForm && (
            <button
              className="primary-job-button"
              onClick={openCreateForm}
            >
              + Post New Job
            </button>
          )}

        </div>

        {jobs.length === 0 ? (

          <div className="empty-jobs">

            <h3>
              No jobs posted yet
            </h3>

            <p>
              Create your first job opening to
              start receiving candidates.
            </p>

            <button
              className="primary-job-button"
              onClick={openCreateForm}
            >
              Post Your First Job
            </button>

          </div>

        ) : (

          <div className="jobs-list">

            {jobs.map((job) => {

              const jobSkills = Array.isArray(job.skills)
                ? job.skills
                : [];

              const jobApplications =
                job.applications ?? 0;

              return (
                <article
                  className="employer-job-card"
                  key={job.id}
                >

                  <div className="job-card-top">

                    <div>

                      <span
                        className={
                          job.status === "ACTIVE"
                            ? "status active"
                            : "status closed"
                        }
                      >
                        {job.status}
                      </span>

                      <h3>
                        {job.title}
                      </h3>

                      <p className="job-location">
                        📍{" "}
                        {job.location ||
                          "Location not specified"}
                      </p>

                    </div>

                    <div className="application-count">

                      <strong>
                        {jobApplications}
                      </strong>

                      <span>
                        Applications
                      </span>

                    </div>

                  </div>

                  {job.description && (
                    <p className="job-description">
                      {job.description}
                    </p>
                  )}

                  <div className="job-details">

                    {job.salary && (
                      <span>
                        💰 {job.salary}
                      </span>
                    )}

                    {job.experience && (
                      <span>
                        🎯 {job.experience}
                      </span>
                    )}

                    {job.employment_type && (
                      <span>
                        💼 {job.employment_type}
                      </span>
                    )}

                  </div>

                  {jobSkills.length > 0 && (
                    <div className="skill-list">

                      {jobSkills.map((skill) => (
                        <span key={skill}>
                          {skill}
                        </span>
                      ))}

                    </div>
                  )}

                  <div className="job-actions">

                    <button
                      className="secondary-button"
                      onClick={() =>
                        openEditForm(job)
                      }
                      disabled={
                        job.status !== "ACTIVE"
                      }
                    >
                      Edit
                    </button>

                    <button
                      className="secondary-button"
                      onClick={() =>
                        navigate(
                          `/employer/applicants?job=${job.id}`
                        )
                      }
                    >
                      View Applicants
                    </button>

                    {job.status === "ACTIVE" && (
                      <button
                        className="danger-button"
                        onClick={() =>
                          closeJob(job.id)
                        }
                      >
                        Close Job
                      </button>
                    )}

                  </div>

                </article>
              );
            })}

          </div>
        )}

      </section>

    </div>
  );
}

export default EmployerDashboard;
