import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./EmployerApplicants.css";

function EmployerApplicants() {
  const navigate = useNavigate();

  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addingToTalentPool, setAddingToTalentPool] = useState(null);

  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedStatus, setSelectedStatus] = useState("");
  const [feedback, setFeedback] = useState("");
  const [saving, setSaving] = useState(false);

  const loadApplications = async () => {
    try {
      setLoading(true);

      const response = await API.get("/employer/applications");

      setApplications(response.data.applications || []);
      setError("");
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Unable to load applications."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const openStatusEditor = (application) => {
    setSelectedApplication(application);
    setSelectedStatus(application.status);
    setFeedback("");
  };

  const closeStatusEditor = () => {
    if (!saving) {
      setSelectedApplication(null);
      setSelectedStatus("");
      setFeedback("");
    }
  };

  const updateStatus = async () => {
    if (!selectedApplication) {
      return;
    }

    try {
      setSaving(true);

      await API.patch(
        `/employer/applications/${selectedApplication.application_id}/status`,
        {
          status: selectedStatus,
          feedback: feedback.trim() || null,
        }
      );

      setSelectedApplication(null);
      setSelectedStatus("");
      setFeedback("");

      await loadApplications();
    } catch (err) {
      console.error(err);

      alert(
        err.response?.data?.detail ||
          "Unable to update application status."
      );
    } finally {
      setSaving(false);
    }
  };

  const getFitClass = (score) => {
    if (score === null || score === undefined) {
      return "fit-neutral";
    }

    if (score >= 80) {
      return "fit-high";
    }

    if (score >= 60) {
      return "fit-medium";
    }

    return "fit-low";
  };

  if (loading) {
  
  const addToTalentPool = async (application) => {
    const candidateId =
      application.candidate_id ??
      application.candidate?.id;

    const applicationId =
      application.application_id ??
      application.id;

    if (!candidateId) {
      alert("Candidate information is unavailable.");
      return;
    }

    setAddingToTalentPool(applicationId);

    try {
      await API.post("/talent-pool/", {
        candidate_id: candidateId,
        application_id: applicationId,
        notes: `Previously considered for ${application.job_title || "a job"}.`,
      });

      alert("Candidate added to talent pool.");
    } catch (err) {
      alert(
        err.response?.data?.detail ||
        "Unable to add candidate to talent pool."
      );
    } finally {
      setAddingToTalentPool(null);
    }
  };

  return (
      <div className="employer-applicants-page">
        <div className="employer-applicants-loading">
          Loading applications...
        </div>
      </div>
    );
  }

  return (
    <div className="employer-applicants-page">
      <div className="employer-applicants-header">
        <div>
          <p className="employer-section-label">
            Hiring intelligence
          </p>

          <h1>Candidate Applications</h1>

          <p>
            Review candidates, AI fit intelligence, application
            status and hiring history.
          </p>
        </div>

        <button
          className="back-button"
          onClick={() => navigate("/employer")}
        >
          Back to Dashboard
        </button>
      </div>

      {error && (
        <div className="employer-applicants-error">
          {error}
        </div>
      )}

      {applications.length === 0 ? (
        <div className="empty-applications">
          <h2>No applications yet</h2>
          <p>
            Applications will appear here when candidates apply
            to your jobs.
          </p>
        </div>
      ) : (
        <div className="applications-table-wrapper">
          <table className="applications-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Job</th>
                <th>AI Fit</th>
                <th>Readiness</th>
                <th>Status</th>
                <th>Applied</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {applications.map((application) => (
                <tr key={application.application_id}>
                  <td>
                    <div className="candidate-table-name">
                      {application.candidate_name || "Unknown"}
                    </div>

                    <div className="candidate-table-email">
                      {application.candidate_email || "—"}
                    </div>

                    {application.candidate_location && (
                      <div className="candidate-table-location">
                        {application.candidate_location}
                      </div>
                    )}
                  </td>

                  <td>
                    <strong>
                      {application.job_title || "Unknown Job"}
                    </strong>
                  </td>

                  <td>
                    <span
                      className={`fit-badge ${getFitClass(
                        application.match_score
                      )}`}
                    >
                      {application.match_score !== null &&
                      application.match_score !== undefined
                        ? `${application.match_score}%`
                        : "N/A"}
                    </span>
                  </td>

                  <td>
                    {application.readiness || "Not Calculated"}
                  </td>

                  <td>
                    <span className="status-badge">
                      {application.status}
                    </span>
                  </td>

                  <td>
                    {application.applied_at
                      ? new Date(
                          application.applied_at
                        ).toLocaleDateString()
                      : "—"}
                  </td>

                  <td>
                    <div className="application-action-buttons">
                      <button
                        className="view-applicant-button"
                        onClick={() =>
                          navigate(
                            `/employer/applicants/${application.application_id}`
                          )
                        }
                      >
                        Intelligence
                      </button>

                      <button
                        className="status-update-button"
                        onClick={() =>
                          openStatusEditor(application)
                        }
                      >
                        Update Status
                      </button>
                <button
                  className="talent-pool-add-button"
                  onClick={() => addToTalentPool(application)}
                  disabled={
                    addingToTalentPool ===
                    (application.application_id ?? application.id)
                  }
                >
                  {
                    addingToTalentPool ===
                    (application.application_id ?? application.id)
                      ? "Adding..."
                      : "Add to Talent Pool"
                  }
                </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedApplication && (
        <div className="status-modal-overlay">
          <div className="status-modal">
            <div className="status-modal-header">
              <div>
                <p>Application update</p>

                <h2>
                  {selectedApplication.candidate_name}
                </h2>

                <span>
                  {selectedApplication.job_title}
                </span>
              </div>

              <button
                className="modal-close-button"
                onClick={closeStatusEditor}
                disabled={saving}
              >
                ×
              </button>
            </div>

            <div className="status-current">
              Current status:
              <strong>
                {selectedApplication.status}
              </strong>
            </div>

            <label className="form-label">
              New status
            </label>

            <select
              className="status-select"
              value={selectedStatus}
              onChange={(event) =>
                setSelectedStatus(event.target.value)
              }
              disabled={saving}
            >
              <option value="APPLIED">APPLIED</option>
              <option value="SCREENING">SCREENING</option>
              <option value="SHORTLISTED">
                SHORTLISTED
              </option>
              <option value="INTERVIEW">INTERVIEW</option>
              <option value="OFFER">OFFER</option>
              <option value="HIRED">HIRED</option>
              <option value="REJECTED">REJECTED</option>
            </select>

            <label className="form-label">
              Employer feedback
            </label>

            <textarea
              className="feedback-textarea"
              value={feedback}
              onChange={(event) =>
                setFeedback(event.target.value)
              }
              maxLength={2000}
              placeholder="Add feedback for this status change. For example: Your backend experience matches the role requirements. We would like to schedule an interview."
              disabled={saving}
            />

            <div className="feedback-counter">
              {feedback.length}/2000
            </div>

            <div className="status-modal-actions">
              <button
                className="cancel-status-button"
                onClick={closeStatusEditor}
                disabled={saving}
              >
                Cancel
              </button>

              <button
                className="save-status-button"
                onClick={updateStatus}
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : "Save Status & Feedback"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default EmployerApplicants;
