import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";

export default function UploadJob() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    title: "",
    description: "",
    location: "",
    salary: "",
    experience: "",
    employment_type: "Full-time",
    skills: "",
  });

  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setAnalysis(null);
    setError("");
    setSuccess("");
  };

  const buildPayload = () => ({
    title: form.title.trim(),
    description: form.description.trim(),
    location: form.location.trim() || null,
    salary: form.salary.trim() || null,
    experience: form.experience.trim() || null,
    employment_type: form.employment_type || null,
    skills: form.skills
      .split(",")
      .map((skill) => skill.trim())
      .filter(Boolean),
  });

  const analyzeJob = async () => {
    setAnalyzing(true);
    setError("");
    setSuccess("");

    try {
      const response = await API.post(
        "/job-quality/analyze",
        buildPayload()
      );

      setAnalysis(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to analyze this job."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const publishJob = async () => {
    if (!analysis) {
      setError("Analyze the job before publishing it.");
      return;
    }

    if (analysis.score < 45) {
      setError(
        "This job needs more information before it can be published."
      );
      return;
    }

    setPublishing(true);
    setError("");
    setSuccess("");

    try {
      await API.post("/jobs/", buildPayload());

      setSuccess("Job published successfully.");

      setTimeout(() => {
        navigate("/employer");
      }, 1000);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to publish the job."
      );
    } finally {
      setPublishing(false);
    }
  };

  const getStatusClass = (status) => {
    if (status === "GOOD") return "quality-good";
    if (status === "FAIR") return "quality-fair";
    if (status === "MISSING") return "quality-missing";
    return "quality-improve";
  };

  return (
    <div className="upload-job-page">
      <div className="upload-job-header">
        <div>
          <span className="quality-label">
            EMPLOYER INTELLIGENCE
          </span>

          <h1>Create a Job</h1>

          <p>
            Create a clear job posting and analyze its quality
            before publishing it to candidates.
          </p>
        </div>
      </div>

      <div className="upload-job-layout">
        <section className="upload-job-form">
          <div className="form-section">
            <h2>Job Information</h2>

            <label>Job Title</label>
            <input
              value={form.title}
              onChange={(e) =>
                updateField("title", e.target.value)
              }
              placeholder="e.g. Python Backend Developer"
            />

            <label>Description</label>
            <textarea
              value={form.description}
              onChange={(e) =>
                updateField("description", e.target.value)
              }
              placeholder="Describe the role, responsibilities, expectations and qualifications..."
              rows={8}
            />

            <label>Required Skills</label>
            <input
              value={form.skills}
              onChange={(e) =>
                updateField("skills", e.target.value)
              }
              placeholder="Python, FastAPI, PostgreSQL, Git"
            />

            <small>
              Separate skills with commas.
            </small>
          </div>

          <div className="form-section">
            <h2>Job Details</h2>

            <label>Location</label>
            <input
              value={form.location}
              onChange={(e) =>
                updateField("location", e.target.value)
              }
              placeholder="Bengaluru, India"
            />

            <label>Salary</label>
            <input
              value={form.salary}
              onChange={(e) =>
                updateField("salary", e.target.value)
              }
              placeholder="₹6,00,000 - ₹10,00,000"
            />

            <label>Experience</label>
            <input
              value={form.experience}
              onChange={(e) =>
                updateField("experience", e.target.value)
              }
              placeholder="1-3 years"
            />

            <label>Employment Type</label>
            <select
              value={form.employment_type}
              onChange={(e) =>
                updateField(
                  "employment_type",
                  e.target.value
                )
              }
            >
              <option value="Full-time">Full-time</option>
              <option value="Part-time">Part-time</option>
              <option value="Contract">Contract</option>
              <option value="Internship">Internship</option>
              <option value="Temporary">Temporary</option>
            </select>
          </div>

          <div className="job-form-actions">
            <button
              className="analyze-job-button"
              onClick={analyzeJob}
              disabled={analyzing}
            >
              {analyzing
                ? "Analyzing..."
                : "Analyze Job Quality"}
            </button>

            <button
              className="publish-job-button"
              onClick={publishJob}
              disabled={
                publishing ||
                !analysis ||
                analysis.score < 45
              }
            >
              {publishing
                ? "Publishing..."
                : "Publish Job"}
            </button>
          </div>

          {error && (
            <div className="job-error">
              {error}
            </div>
          )}

          {success && (
            <div className="job-success">
              {success}
            </div>
          )}
        </section>

        <aside className="quality-panel">
          {!analysis ? (
            <div className="quality-empty">
              <div className="quality-icon">AI</div>

              <h2>Job Quality Analyzer</h2>

              <p>
                Complete the job information and click
                <strong> Analyze Job Quality </strong>
                to check the posting before publishing.
              </p>

              <div className="quality-check-preview">
                <span>✓ Job title</span>
                <span>✓ Description</span>
                <span>✓ Required skills</span>
                <span>✓ Experience</span>
                <span>✓ Location</span>
                <span>✓ Salary</span>
                <span>✓ Employment type</span>
              </div>
            </div>
          ) : (
            <div className="quality-results">
              <div className="quality-score">
                <span>Job Quality</span>
                <strong>{analysis.score}</strong>
                <small>/ 100</small>
                <b>{analysis.quality}</b>
              </div>

              <div className="quality-summary">
                <div>
                  <strong>{analysis.skills_count}</strong>
                  <span>Skills</span>
                </div>

                <div>
                  <strong>
                    {analysis.description_word_count}
                  </strong>
                  <span>Description words</span>
                </div>
              </div>

              <h3>Quality Checks</h3>

              <div className="quality-checks">
                {analysis.checks.map((check) => (
                  <div
                    className="quality-check"
                    key={check.name}
                  >
                    <div>
                      <strong>{check.name}</strong>
                      <p>{check.message}</p>
                    </div>

                    <span
                      className={getStatusClass(
                        check.status
                      )}
                    >
                      {check.status}
                    </span>
                  </div>
                ))}
              </div>

              {analysis.suggestions.length > 0 && (
                <>
                  <h3>Suggestions</h3>

                  <div className="quality-suggestions">
                    {analysis.suggestions.map(
                      (suggestion, index) => (
                        <div key={index}>
                          <span>→</span>
                          <p>{suggestion}</p>
                        </div>
                      )
                    )}
                  </div>
                </>
              )}

              {analysis.score >= 85 && (
                <div className="quality-ready">
                  ✓ This job has sufficient information
                  for publishing.
                </div>
              )}

              {analysis.score >= 45 &&
                analysis.score < 85 && (
                  <div className="quality-warning">
                    The job can be published, but the
                    suggestions above may improve its
                    clarity.
                  </div>
                )}

              {analysis.score < 45 && (
                <div className="quality-blocked">
                  Publishing is blocked until the job
                  contains more complete information.
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
