import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import API from "../services/api";
import "./Companies.css";

function Companies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadCompanies = async () => {
      try {
        const response = await API.get("/companies/");
        setCompanies(response.data);
      } catch (err) {
        console.error(err);
        setError(
          err.response?.data?.detail ||
            "Unable to load companies."
        );
      } finally {
        setLoading(false);
      }
    };

    loadCompanies();
  }, []);

  if (loading) {
    return (
      <div className="companies-page">
        <div className="companies-state">
          Loading companies...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="companies-page">
        <div className="companies-state companies-error">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="companies-page">
      <header className="companies-header">
        <span className="companies-eyebrow">
          Explore employers
        </span>

        <h1>Companies</h1>

        <p>
          Explore companies hiring through the platform and
          discover their current opportunities.
        </p>
      </header>

      {companies.length === 0 ? (
        <div className="companies-state">
          No companies are available yet.
        </div>
      ) : (
        <section className="companies-grid">
          {companies.map((company) => (
            <article
              className="company-card"
              key={company.id}
            >
              <div className="company-card-header">
                <div className="company-logo">
                  {company.name?.charAt(0)?.toUpperCase() || "C"}
                </div>

                <div>
                  <h2>{company.name}</h2>

                  {company.location && (
                    <p className="company-location">
                      {company.location}
                    </p>
                  )}
                </div>
              </div>

              <p className="company-description">
                {company.description ||
                  "Company information is not available yet."}
              </p>

              <div className="company-card-footer">
                <span>
                  {company.active_jobs || 0} active{" "}
                  {company.active_jobs === 1
                    ? "job"
                    : "jobs"}
                </span>

                <Link
                  to={`/companies/${company.id}`}
                  className="company-view-button"
                >
                  View company
                </Link>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}

export default Companies;
