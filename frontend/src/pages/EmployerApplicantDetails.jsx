import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../services/api";
import "./EmployerApplicantDetails.css";

function EmployerApplicantDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDetails = async () => {
    try {
      const user = JSON.parse(
        localStorage.getItem("user") || "null"
      );

      if (!user || user.role !== "EMPLOYER_USER") {
        navigate("/login");
        return;
      }

      const response = await API.get(
        `/employer/applications/${id}`
      );

      setData(response.data);
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
        "Unable to load candidate intelligence."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetails();
  }, [id]);

  const updateStatus = async (status) => {
    try {
      await API.patch(
        `/employer/applications/${id}/status`,
        { status }
      );

      setData((current) => ({
        ...current,
        status,
      }));
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to update application status."
      );
    }
  };

  if (loading) {
    return (
      <div className="applicant-intelligence-page">
        <div className="intelligence-loading">
          Loading candidate intelligence...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="applicant-intelligence-page">
        <div className="intelligence-error">
          {error}
        </div>

        <button
          onClick={() => navigate("/employer/applicants")}
        >
          Back to Applicants
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const {
    application_id,
    job,
    candidate,
    resume,
    intelligence,
    status,
    applied_at,
  } = data;

  const score =
    intelligence?.career_fit_score ??
    intelligence?.score;

  return (
    <div className="applicant-intelligence-page">

      <div className="intelligence-header">

        <div>
          <span className="intelligence-eyebrow">
            AI CANDIDATE INTELLIGENCE
          </span>

          <h1>{candidate.name}</h1>

          <p>
            {job.title} · {candidate.email}
          </p>
        </div>

        <button
          className="intelligence-back"
          onClick={() =>
            navigate("/employer/applicants")
          }
        >
          ← Back to Applicants
        </button>

      </div>

      <div className="candidate-top-grid">

        <div className="score-card">

          <span className="card-label">
            AI FIT SCORE
          </span>

          <strong className="fit-score">
            {score !== null && score !== undefined
              ? `${score}%`
              : "N/A"}
          </strong>

          <span className="readiness">
            {intelligence?.readiness ||
              "Not Calculated"}
          </span>

        </div>

        <div className="candidate-overview-card">

          <span className="card-label">
            APPLICATION
          </span>

          <h3>{job.title}</h3>

          <p>
            Applied{" "}
            {new Date(
              applied_at
            ).toLocaleDateString()}
          </p>

          <select
            value={status}
            onChange={(event) =>
              updateStatus(event.target.value)
            }
          >
            <option value="APPLIED">Applied</option>
            <option value="SCREENING">Screening</option>
            <option value="SHORTLISTED">
              Shortlisted
            </option>
            <option value="INTERVIEW">
              Interview
            </option>
            <option value="OFFER">Offer</option>
            <option value="HIRED">Hired</option>
            <option value="REJECTED">
              Rejected
            </option>
          </select>

        </div>

      </div>

      <div className="intelligence-grid">

        <section className="intelligence-card">

          <h2>Why this candidate fits</h2>

          <p className="intelligence-explanation">
            {intelligence?.explanation ||
              "No explanation available."}
          </p>

          <h3>Matching Skills</h3>

          {intelligence?.matching_skills?.length ? (
            <div className="skill-list">
              {intelligence.matching_skills.map(
                (skill) => (
                  <span
                    className="skill-match"
                    key={skill}
                  >
                    ✓ {skill}
                  </span>
                )
              )}
            </div>
          ) : (
            <p className="muted">
              No matching skills detected.
            </p>
          )}

        </section>

        <section className="intelligence-card">

          <h2>Skill Gaps</h2>

          {intelligence?.missing_skills?.length ? (
            <div className="skill-list">
              {intelligence.missing_skills.map(
                (skill) => (
                  <span
                    className="skill-missing"
                    key={skill}
                  >
                    {skill}
                  </span>
                )
              )}
            </div>
          ) : (
            <p className="muted">
              No missing skills detected.
            </p>
          )}

        </section>

      </div>

      <div className="intelligence-grid">

        <section className="intelligence-card">

          <h2>Candidate Profile</h2>

          <div className="profile-item">
            <span>Location</span>
            <strong>
              {candidate.location || "Not provided"}
            </strong>
          </div>

          <div className="profile-item">
            <span>Phone</span>
            <strong>
              {candidate.phone || "Not provided"}
            </strong>
          </div>

          <div className="profile-item">
            <span>Experience</span>
            <p>
              {candidate.experience ||
                "Not provided"}
            </p>
          </div>

          <div className="profile-item">
            <span>Education</span>
            <p>
              {candidate.education ||
                "Not provided"}
            </p>
          </div>

          <div className="profile-item">
            <span>Bio</span>
            <p>
              {candidate.bio || "Not provided"}
            </p>
          </div>

        </section>

        <section className="intelligence-card">

          <h2>Resume Intelligence</h2>

          {resume ? (
            <>
              <div className="resume-name">
                {resume.original_filename}
              </div>

              <div className="resume-status">
                Status: {resume.status}
              </div>

              <h3>Detected Skills</h3>

              {intelligence?.resume_skills?.length ? (
                <div className="skill-list">
                  {intelligence.resume_skills.map(
                    (skill) => (
                      <span
                        className="skill-resume"
                        key={skill}
                      >
                        {skill}
                      </span>
                    )
                  )}
                </div>
              ) : (
                <p className="muted">
                  No known skills detected.
                </p>
              )}
            </>
          ) : (
            <div className="no-resume">
              This candidate did not attach a
              resume to the application.
            </div>
          )}

        </section>

      </div>

      <section className="intelligence-card recommendations-card">

        <h2>AI Recommendations</h2>

        {intelligence?.recommendations?.length ? (
          <ul>
            {intelligence.recommendations.map(
              (recommendation) => (
                <li key={recommendation}>
                  {recommendation}
                </li>
              )
            )}
          </ul>
        ) : (
          <p className="muted">
            No additional skill recommendations.
          </p>
        )}

      </section>

      <div className="intelligence-footer">

        <button
          className="secondary-action"
          onClick={() =>
            navigate("/employer/applicants")
          }
        >
          Back to Applicants
        </button>

        <button
          className="primary-action"
          onClick={() =>
            updateStatus("SHORTLISTED")
          }
        >
          Shortlist Candidate
        </button>

      </div>

    </div>
  );
}

export default EmployerApplicantDetails;
