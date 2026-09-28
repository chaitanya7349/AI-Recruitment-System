import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../services/api";
import "./JobDetails.css";

function JobDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJob();
  }, [id]);

  const fetchJob = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await API.get(`/jobs/${id}`);

      setJob(response.data);
    } catch (err) {
      console.error("Failed to fetch job:", err);
      setError("Unable to load this job.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="job-details-state">
        <div className="loader"></div>
        <p>Loading job details...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="job-details-state">
        <h2>Job not found</h2>
        <p>{error || "This job is no longer available."}</p>

        <button onClick={() => navigate("/jobs")}>
          ← Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="job-details-page">
      <div className="job-details-container">

        <button
          className="back-button"
          onClick={() => navigate("/jobs")}
        >
          ← Back to Jobs
        </button>

        <div className="job-details-layout">

          <main className="job-details-main">

            <div className="job-company-header">
              <div className="large-company-logo">
                {job.company_name?.charAt(0)?.toUpperCase() || "C"}
              </div>

              <div>
                <h1>{job.title}</h1>

                <p className="details-company">
                  {job.company_name}
                </p>

                <p className="details-location">
                  📍 {job.location || "Location not specified"}
                </p>
              </div>
            </div>

            <div className="job-info-tags">

              {job.experience && (
                <span>
                  Experience: {job.experience}
                </span>
              )}

              {job.employment_type && (
                <span>
                  {job.employment_type}
                </span>
              )}

              {job.salary && (
                <span>
                  {job.salary}
                </span>
              )}

            </div>

            <section className="details-section">
              <h2>Job Description</h2>

              <p>{job.description}</p>
            </section>

            {job.skills?.length > 0 && (
              <section className="details-section">
                <h2>Required Skills</h2>

                <div className="details-skills">
                  {job.skills.map((skill) => (
                    <span key={skill}>
                      {skill}
                    </span>
                  ))}
                </div>
              </section>
            )}

          </main>

          <aside className="job-apply-card">

            <h2>Interested in this role?</h2>

            <p>
              Apply for this opportunity and let our AI career
              intelligence system help you understand your fit.
            </p>

            <button
              className="apply-button"
              onClick={() => {
                alert("Application flow will be connected next.");
              }}
            >
              Apply for this Job
            </button>

            <button
              className="career-fit-button"
              onClick={() => navigate("/career-fit")}
            >
              Check Career Fit
            </button>

            <div className="apply-card-note">
              <strong>AI Career Intelligence</strong>

              <p>
                Understand matching skills, missing skills and
                areas you can improve before applying.
              </p>
            </div>

          </aside>

        </div>
      </div>
    </div>
  );
}

export default JobDetails;
