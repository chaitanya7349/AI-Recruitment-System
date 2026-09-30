import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import API from "../services/api";
import "./CareerFit.css";

function CareerFit() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const jobId = searchParams.get("job");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadFit = async () => {
      if (!jobId) {
        setError("Select a job to calculate career fit.");
        setLoading(false);
        return;
      }

      try {
        const response = await API.get(
          `/candidate/jobs/${jobId}/fit`
        );

        setResult(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Unable to calculate career fit."
        );
      } finally {
        setLoading(false);
      }
    };

    loadFit();
  }, [jobId]);

  if (loading) {
    return (
      <div className="career-fit-loading">
        Analyzing your career fit...
      </div>
    );
  }

  if (error) {
    return (
      <div className="career-fit-page">
        <div className="career-fit-error">
          <h2>Career Fit unavailable</h2>

          <p>{error}</p>

          <button
            onClick={() =>
              navigate("/candidate-dashboard")
            }
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const fit = result.fit;

  return (
    <div className="career-fit-page">

      <div className="career-fit-header">

        <button
          onClick={() =>
            navigate("/candidate-dashboard")
          }
          className="career-back"
        >
          ← Dashboard
        </button>

        <span>
          AI CAREER INTELLIGENCE
        </span>

        <h1>
          Your Career Fit
        </h1>

        <p>
          {result.job_title || "Selected Job"}
        </p>

      </div>

      <div className="career-fit-score-card">

        <div className="score-circle">

          <strong>
            {fit.score}%
          </strong>

          <span>
            Fit
          </span>

        </div>

        <div className="score-content">

          <span className="fit-label">
            {fit.readiness}
          </span>

          <h2>
            How well your resume matches this role
          </h2>

          <p>
            This score is based on skills detected
            in your resume compared with the skills
            required for this job.
          </p>

        </div>

      </div>

      <div className="career-fit-grid">

        <section className="fit-card">

          <h2>
            ✓ Matching Skills
          </h2>

          {fit.matching_skills.length === 0 ? (
            <p className="empty-fit">
              No matching skills detected yet.
            </p>
          ) : (
            <div className="fit-tags matching">
              {fit.matching_skills.map(
                (skill) => (
                  <span key={skill}>
                    {skill}
                  </span>
                )
              )}
            </div>
          )}

        </section>

        <section className="fit-card">

          <h2>
            + Skills to Develop
          </h2>

          {fit.missing_skills.length === 0 ? (
            <p className="empty-fit">
              No missing skills detected.
            </p>
          ) : (
            <div className="fit-tags missing">
              {fit.missing_skills.map(
                (skill) => (
                  <span key={skill}>
                    {skill}
                  </span>
                )
              )}
            </div>
          )}

        </section>

      </div>

      <section className="fit-card">

        <h2>
          Skill Gap → Action
        </h2>

        {fit.recommendations.length === 0 ? (
          <p>
            Your detected skills cover the current
            requirements.
          </p>
        ) : (
          <div className="recommendation-list">

            {fit.recommendations.map(
              (recommendation, index) => (
                <div
                  key={index}
                  className="recommendation"
                >
                  <strong>
                    {index + 1}
                  </strong>

                  <span>
                    {recommendation}
                  </span>
                </div>
              )
            )}

          </div>
        )}

      </section>

      <section className="fit-card resume-skills-card">

        <h2>
          Skills Detected From Your Resume
        </h2>

        <div className="fit-tags">
          {fit.resume_skills.map(
            (skill) => (
              <span key={skill}>
                {skill}
              </span>
            )
          )}
        </div>

      </section>

    </div>
  );
}

export default CareerFit;
