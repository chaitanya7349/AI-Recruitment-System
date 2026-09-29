import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./HiringPipeline.css";

const STAGES = [
  "APPLIED",
  "SCREENING",
  "SHORTLISTED",
  "INTERVIEW",
  "OFFER",
  "HIRED",
];

const stageLabels = {
  APPLIED: "Applied",
  SCREENING: "Screening",
  SHORTLISTED: "Shortlisted",
  INTERVIEW: "Interview",
  OFFER: "Offer",
  HIRED: "Hired",
};

function HiringPipeline() {
  const navigate = useNavigate();

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadApplications = async () => {
    try {
      const user = JSON.parse(
        localStorage.getItem("user") || "null"
      );

      const token = localStorage.getItem("token");

      if (!token || !user || user.role !== "EMPLOYER_USER") {
        navigate("/login");
        return;
      }

      const response = await API.get(
        "/employer/applications"
      );

      setApplications(
        response.data.applications || []
      );
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
          "Unable to load hiring pipeline."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const updateStatus = async (
    applicationId,
    status
  ) => {
    try {
      await API.patch(
        `/employer/applications/${applicationId}/status`,
        { status }
      );

      setApplications((current) =>
        current.map((application) =>
          application.application_id === applicationId
            ? {
                ...application,
                status,
              }
            : application
        )
      );
    } catch (err) {
      alert(
        err.response?.data?.detail ||
          "Unable to update candidate stage."
      );
    }
  };

  const getNextStage = (status) => {
    const index = STAGES.indexOf(status);

    if (
      index === -1 ||
      index === STAGES.length - 1
    ) {
      return null;
    }

    return STAGES[index + 1];
  };

  if (loading) {
    return (
      <div className="pipeline-page">
        <div className="pipeline-loading">
          Loading hiring pipeline...
        </div>
      </div>
    );
  }

  return (
    <div className="pipeline-page">

      <header className="pipeline-header">

        <div>
          <span className="pipeline-eyebrow">
            HIRING WORKFLOW
          </span>

          <h1>Hiring Pipeline</h1>

          <p>
            Track candidates through every stage
            of your hiring process.
          </p>
        </div>

        <div className="pipeline-header-actions">

          <button
            className="pipeline-secondary-button"
            onClick={() =>
              navigate("/employer/applicants")
            }
          >
            Applicants
          </button>

          <button
            className="pipeline-secondary-button"
            onClick={() =>
              navigate("/employer")
            }
          >
            Dashboard
          </button>

        </div>

      </header>

      {error && (
        <div className="pipeline-error">
          {error}
        </div>
      )}

      <div className="pipeline-board">

        {STAGES.map((stage) => {

          const stageApplications =
            applications.filter(
              (application) =>
                application.status === stage
            );

          return (
            <section
              className="pipeline-column"
              key={stage}
            >

              <div className="pipeline-column-header">

                <div>
                  <span className="pipeline-stage-dot" />

                  <h2>
                    {stageLabels[stage]}
                  </h2>
                </div>

                <span className="pipeline-count">
                  {stageApplications.length}
                </span>

              </div>

              <div className="pipeline-cards">

                {stageApplications.length === 0 ? (

                  <div className="pipeline-empty">
                    No candidates
                  </div>

                ) : (

                  stageApplications.map(
                    (application) => {

                      const nextStage =
                        getNextStage(
                          application.status
                        );

                      return (
                        <article
                          className="pipeline-card"
                          key={
                            application.application_id
                          }
                        >

                          <div className="pipeline-card-top">

                            <div>
                              <h3>
                                {
                                  application.candidate_name
                                }
                              </h3>

                              <span>
                                {
                                  application.job_title
                                }
                              </span>
                            </div>

                            <strong className="pipeline-score">
                              {application.match_score !==
                                null &&
                              application.match_score !==
                                undefined
                                ? `${application.match_score}%`
                                : "N/A"}
                            </strong>

                          </div>

                          <div className="pipeline-readiness">

                            {application.readiness ||
                              "Not Calculated"}

                          </div>

                          {application.matching_skills
                            ?.length > 0 && (

                            <div className="pipeline-skills">

                              <span className="skills-title">
                                Matching
                              </span>

                              <div>
                                {application.matching_skills
                                  .slice(0, 4)
                                  .map((skill) => (
                                    <span
                                      className="pipeline-skill-match"
                                      key={skill}
                                    >
                                      {skill}
                                    </span>
                                  ))}
                              </div>

                            </div>
                          )}

                          {application.missing_skills
                            ?.length > 0 && (

                            <div className="pipeline-skills">

                              <span className="skills-title">
                                Gaps
                              </span>

                              <div>
                                {application.missing_skills
                                  .slice(0, 3)
                                  .map((skill) => (
                                    <span
                                      className="pipeline-skill-gap"
                                      key={skill}
                                    >
                                      {skill}
                                    </span>
                                  ))}
                              </div>

                            </div>
                          )}

                          <div className="pipeline-date">

                            Applied{" "}
                            {new Date(
                              application.applied_at
                            ).toLocaleDateString()}

                          </div>

                          <div className="pipeline-actions">

                            <button
                              className="view-intelligence-button"
                              onClick={() =>
                                navigate(
                                  `/employer/applicants/${application.application_id}`
                                )
                              }
                            >
                              View Intelligence
                            </button>

                            {nextStage && (
                              <button
                                className="next-stage-button"
                                onClick={() =>
                                  updateStatus(
                                    application.application_id,
                                    nextStage
                                  )
                                }
                              >
                                →{" "}
                                {
                                  stageLabels[
                                    nextStage
                                  ]
                                }
                              </button>
                            )}

                          </div>

                        </article>
                      );
                    }
                  )
                )}

              </div>

            </section>
          );
        })}

      </div>

      <section className="rejected-section">

        <div className="rejected-header">

          <div>
            <span className="pipeline-eyebrow">
              CLOSED
            </span>

            <h2>Rejected Candidates</h2>
          </div>

          <span className="rejected-count">
            {
              applications.filter(
                (application) =>
                  application.status === "REJECTED"
              ).length
            }
          </span>

        </div>

        <div className="rejected-list">

          {applications
            .filter(
              (application) =>
                application.status === "REJECTED"
            )
            .map((application) => (

              <div
                className="rejected-card"
                key={application.application_id}
              >

                <div>
                  <strong>
                    {application.candidate_name}
                  </strong>

                  <span>
                    {application.job_title}
                  </span>
                </div>

                <span>
                  {application.match_score !== null &&
                  application.match_score !== undefined
                    ? `${application.match_score}% fit`
                    : "Fit not calculated"}
                </span>

                <button
                  onClick={() =>
                    navigate(
                      `/employer/applicants/${application.application_id}`
                    )
                  }
                >
                  View
                </button>

              </div>

            ))}

          {applications.filter(
            (application) =>
              application.status === "REJECTED"
          ).length === 0 && (
            <p className="no-rejected">
              No rejected candidates.
            </p>
          )}

        </div>

      </section>

    </div>
  );
}

export default HiringPipeline;
