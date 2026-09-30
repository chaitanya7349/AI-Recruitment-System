import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../services/api";
import "./SkillGap.css";

export default function SkillGap() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!jobId) {
      setError("No job selected.");
      setLoading(false);
      return;
    }

    loadSkillGap();
  }, [jobId]);

  const loadSkillGap = async () => {
    try {
      const response = await API.get(`/candidate/jobs/${jobId}/fit`);
      const result = response.data;

      const fit = result.fit || {};

      const actions = (fit.recommendations || []).map(
        (recommendation, index) => ({
          skill: fit.missing_skills?.[index] || "Skill Development",
          priority: index === 0 ? "HIGH" : "MEDIUM",
          action: recommendation,
          project: `Build a practical project using ${
            fit.missing_skills?.[index] || "this skill"
          }.`,
        })
      );

      setData({
        job_id: result.job_id,
        job_title: result.job_title,
        career_fit_score: fit.score ?? 0,
        readiness: fit.readiness || "Needs Improvement",
        matching_skills: fit.matching_skills || [],
        missing_skills: fit.missing_skills || [],
        actions,
        skill_gap_count: (fit.missing_skills || []).length,
        message:
          fit.missing_skills?.length > 0
            ? "These are the main skills you can develop to improve your fit for this role."
            : "Your detected skills currently cover the requirements for this role.",
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load skill gap analysis."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="skill-gap-page">
        <div className="skill-gap-loading">
          Analyzing your career skill gap...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="skill-gap-page">
        <div className="skill-gap-error">
          <h2>Skill Gap Analysis</h2>
          <p>{error}</p>
          <button onClick={() => navigate("/candidate-dashboard")}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="skill-gap-page">
      <div className="skill-gap-header">
        <div>
          <span className="skill-gap-label">
            AI CAREER INTELLIGENCE
          </span>

          <h1>Skill Gap → Action</h1>

          <p>
            Identify the skills you are missing for this role and turn
            each gap into a practical improvement plan.
          </p>
        </div>

        <div className="skill-gap-score">
          <span>Career Fit</span>
          <strong>{data.career_fit_score}%</strong>
          <small>{data.readiness}</small>
        </div>
      </div>

      <section className="skill-gap-job-card">
        <span>Target Role</span>
        <h2>{data.job_title}</h2>

        <p>{data.message}</p>
      </section>

      <div className="skill-gap-grid">
        <section className="skill-section">
          <div className="section-heading">
            <h2>Skills You Already Match</h2>
            <span>{data.matching_skills.length}</span>
          </div>

          {data.matching_skills.length === 0 ? (
            <div className="empty-skill">
              No matching skills detected yet.
            </div>
          ) : (
            <div className="skill-list matched">
              {data.matching_skills.map((skill) => (
                <div className="skill-chip" key={skill}>
                  ✓ {skill}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="skill-section">
          <div className="section-heading">
            <h2>Skills to Develop</h2>
            <span>{data.missing_skills.length}</span>
          </div>

          {data.missing_skills.length === 0 ? (
            <div className="success-skill">
              No detected skill gaps.
            </div>
          ) : (
            <div className="skill-list missing">
              {data.missing_skills.map((skill) => (
                <div className="skill-chip" key={skill}>
                  + {skill}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="action-plan">
        <div className="action-plan-header">
          <div>
            <span className="skill-gap-label">
              PERSONALIZED DEVELOPMENT PLAN
            </span>
            <h2>Turn Skill Gaps Into Actions</h2>
          </div>

          <span className="gap-count">
            {data.skill_gap_count} gaps detected
          </span>
        </div>

        {data.actions.length === 0 ? (
          <div className="no-actions">
            You currently have no detected skill gaps for this role.
          </div>
        ) : (
          <div className="action-list">
            {data.actions.map((item, index) => (
              <div className="action-card" key={item.skill}>
                <div className="action-number">
                  {index + 1}
                </div>

                <div className="action-content">
                  <div className="action-title-row">
                    <h3>{item.skill}</h3>

                    <span
                      className={`priority ${item.priority.toLowerCase()}`}
                    >
                      {item.priority} PRIORITY
                    </span>
                  </div>

                  <p>{item.action}</p>

                  <div className="project-suggestion">
                    <strong>Practice project</strong>
                    <span>{item.project}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="skill-gap-actions">
        <button
          className="secondary-button"
          onClick={() =>
            navigate(`/career-fit?job=${data.job_id}`)
          }
        >
          ← Back to Career Fit
        </button>

        <button
          className="primary-button"
          onClick={() =>
            navigate(`/jobs/${data.job_id}`)
          }
        >
          View Job & Apply
        </button>
      </div>
    </div>
  );
}
