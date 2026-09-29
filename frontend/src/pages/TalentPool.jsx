import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./TalentPool.css";

export default function TalentPool() {
  const navigate = useNavigate();

  const [talent, setTalent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTalent();
  }, []);

  const loadTalent = async () => {
    try {
      const response = await API.get("/talent-pool/");
      setTalent(response.data.talent || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load talent pool."
      );
    } finally {
      setLoading(false);
    }
  };

  const removeCandidate = async (entryId) => {
    const confirmed = window.confirm(
      "Remove this candidate from your talent pool?"
    );

    if (!confirmed) return;

    try {
      await API.delete(`/talent-pool/${entryId}`);
      setTalent((current) =>
        current.filter((item) => item.id !== entryId)
      );
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to remove candidate."
      );
    }
  };

  if (loading) {
    return (
      <div className="talent-pool-page">
        <div className="talent-loading">
          Loading talent pool...
        </div>
      </div>
    );
  }

  return (
    <div className="talent-pool-page">
      <div className="talent-header">
        <div>
          <span className="talent-label">
            TALENT RECOVERY
          </span>

          <h1>Talent Pool</h1>

          <p>
            Keep promising candidates available for future
            hiring opportunities instead of losing valuable
            candidate intelligence after one application.
          </p>
        </div>

        <div className="talent-count">
          <strong>{talent.length}</strong>
          <span>Saved Candidates</span>
        </div>
      </div>

      {error && (
        <div className="talent-error">
          {error}
        </div>
      )}

      {talent.length === 0 ? (
        <div className="talent-empty">
          <div className="talent-empty-icon">
            TP
          </div>

          <h2>Your talent pool is empty</h2>

          <p>
            Candidates you want to consider for future
            opportunities will appear here.
          </p>

          <button
            onClick={() =>
              navigate("/employer/applicants")
            }
          >
            Review Applicants
          </button>
        </div>
      ) : (
        <div className="talent-list">
          {talent.map((candidate) => (
            <div
              className="talent-card"
              key={candidate.id}
            >
              <div className="talent-main">
                <div className="talent-avatar">
                  {candidate.candidate_name
                    ?.charAt(0)
                    ?.toUpperCase()}
                </div>

                <div className="talent-info">
                  <h2>{candidate.candidate_name}</h2>

                  <p>
                    {candidate.candidate_email}
                  </p>

                  <div className="talent-meta">
                    {candidate.candidate_location && (
                      <span>
                        📍 {candidate.candidate_location}
                      </span>
                    )}

                    {candidate.candidate_experience && (
                      <span>
                        Experience:{" "}
                        {candidate.candidate_experience}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="talent-intelligence">
                <div className="talent-score">
                  <span>Previous Fit</span>

                  <strong>
                    {candidate.match_score !== null
                      ? `${candidate.match_score}%`
                      : "—"}
                  </strong>

                  <small>
                    {candidate.readiness ||
                      "Not analyzed"}
                  </small>
                </div>

                <div className="talent-source">
                  <span>Previously considered for</span>

                  <strong>
                    {candidate.source_job ||
                      "Candidate pool"}
                  </strong>
                </div>
              </div>

              {candidate.matching_skills?.length > 0 && (
                <div className="talent-skills">
                  <strong>Matching skills</strong>

                  <div>
                    {candidate.matching_skills
                      .slice(0, 6)
                      .map((skill) => (
                        <span key={skill}>
                          {skill}
                        </span>
                      ))}
                  </div>
                </div>
              )}

              {candidate.notes && (
                <div className="talent-notes">
                  <strong>Employer notes</strong>
                  <p>{candidate.notes}</p>
                </div>
              )}

              <div className="talent-actions">
                {candidate.source_application_id && (
                  <button
                    className="talent-view-button"
                    onClick={() =>
                      navigate(
                        `/employer/applicants/${candidate.source_application_id}`
                      )
                    }
                  >
                    View Intelligence
                  </button>
                )}

                <button
                  className="talent-remove-button"
                  onClick={() =>
                    removeCandidate(candidate.id)
                  }
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
