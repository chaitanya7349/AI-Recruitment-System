import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import API from "../services/api";
import "./CompanyDetails.css";

function CompanyDetails() {
  const { id } = useParams();

  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadCompany = async () => {
      try {
        const response = await API.get(`/companies/${id}`);
        setCompany(response.data);
      } catch (err) {
        console.error(err);
        setError(
          err.response?.data?.detail ||
            "Unable to load company details."
        );
      } finally {
        setLoading(false);
      }
    };

    loadCompany();
  }, [id]);

  if (loading) {
    return (
      <div className="company-details-page">
        <div className="company-details-state">
          Loading company...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="company-details-page">
        <div className="company-details-state company-details-error">
          {error}
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="company-details-page">
        <div className="company-details-state">
          Company not found.
        </div>
      </div>
    );
  }

  return (
    <div className="company-details-page">
      <Link to="/companies" className="company-back-link">
        ← Back to companies
      </Link>

      <section className="company-hero">
        <div className="company-hero-logo">
          {company.name?.charAt(0)?.toUpperCase() || "C"}
        </div>

        <div className="company-hero-content">
          <span className="company-details-eyebrow">
            Company profile
          </span>

          <h1>{company.name}</h1>

          {company.location && (
            <p className="company-hero-location">
              {company.location}
            </p>
          )}

          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noreferrer"
              className="company-website"
            >
              Visit company website ↗
            </a>
          )}
        </div>
      </section>

      <section className="company-about">
        <div>
          <span className="company-section-label">About</span>
          <h2>About {company.name}</h2>
        </div>

        <p>
          {company.description ||
            "Company information is not available yet."}
        </p>
      </section>

      <section className="company-jobs">
        <div className="company-jobs-header">
          <div>
            <span className="company-section-label">
              Opportunities
            </span>
            <h2>Open positions</h2>
          </div>

          <span className="company-job-count">
            {company.active_jobs || 0} active{" "}
            {company.active_jobs === 1 ? "job" : "jobs"}
          </span>
        </div>

        {company.jobs?.length === 0 ? (
          <div className="company-details-state">
            This company currently has no active jobs.
          </div>
        ) : (
          <div className="company-job-list">
            {company.jobs.map((job) => (
              <article className="company-job-card" key={job.id}>
                <div className="company-job-main">
                  <h3>{job.title}</h3>

                  <div className="company-job-meta">
                    {job.location && (
                      <span>{job.location}</span>
                    )}

                    {job.employment_type && (
                      <span>{job.employment_type}</span>
                    )}

                    {job.experience && (
                      <span>{job.experience}</span>
                    )}
                  </div>

                  {job.salary && (
                    <p className="company-job-salary">
                      {job.salary}
                    </p>
                  )}
                </div>

                <Link
                  to={`/jobs/${job.id}`}
                  className="company-job-button"
                >
                  View job
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default CompanyDetails;
