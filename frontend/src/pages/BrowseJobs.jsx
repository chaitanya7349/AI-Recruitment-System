import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./BrowseJobs.css";

function BrowseJobs() {
  const navigate = useNavigate();

  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await API.get("/jobs/");

      setJobs(Array.isArray(response.data) ? response.data : (response.data.jobs || []));
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
      setError(
        "Unable to load jobs. Please make sure the backend server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = useMemo(() => {
    const searchText = search.toLowerCase().trim();
    const locationText = location.toLowerCase().trim();

    return jobs.filter((job) => {
      const matchesSearch =
        !searchText ||
        job.title?.toLowerCase().includes(searchText) ||
        job.company_name?.toLowerCase().includes(searchText) ||
        job.skills?.some((skill) =>
          skill.toLowerCase().includes(searchText)
        );

      const matchesLocation =
        !locationText ||
        job.location?.toLowerCase().includes(locationText);

      return matchesSearch && matchesLocation;
    });
  }, [jobs, search, location]);

  return (
    <div className="browse-jobs-page">
      <section className="jobs-header">
        <div className="jobs-header-content">
          <span className="jobs-eyebrow">CAREER OPPORTUNITIES</span>

          <h1>Find work that fits your career.</h1>

          <p>
            Explore real opportunities and discover where your skills can take
            you next.
          </p>

          <div className="job-search-panel">
            <div className="search-field">
              <label>What are you looking for?</label>
              <input
                type="text"
                placeholder="Job title, company or skill"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="search-field">
              <label>Location</label>
              <input
                type="text"
                placeholder="City or location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>

            <button
              className="search-button"
              onClick={() => window.scrollTo({ top: 420, behavior: "smooth" })}
            >
              Search Jobs
            </button>
          </div>
        </div>
      </section>

      <main className="jobs-content">
        <div className="jobs-toolbar">
          <div>
            <h2>Available Jobs</h2>
            <p>
              {loading
                ? "Loading opportunities..."
                : `${filteredJobs.length} opportunities found`}
            </p>
          </div>

          <button className="refresh-button" onClick={fetchJobs}>
            Refresh
          </button>
        </div>

        {loading && (
          <div className="jobs-state">
            <div className="loader"></div>
            <p>Loading jobs from the recruitment platform...</p>
          </div>
        )}

        {!loading && error && (
          <div className="jobs-state error-state">
            <h3>Something went wrong</h3>
            <p>{error}</p>
            <button onClick={fetchJobs}>Try Again</button>
          </div>
        )}

        {!loading && !error && filteredJobs.length === 0 && (
          <div className="jobs-state">
            <h3>No jobs found</h3>
            <p>
              Try changing your search terms or location.
            </p>
          </div>
        )}

        {!loading && !error && filteredJobs.length > 0 && (
          <div className="jobs-grid">
            {filteredJobs.map((job) => (
              <article className="job-card" key={job.id}>
                <div className="job-card-top">
                  <div className="company-logo">
                    {job.company_name?.charAt(0)?.toUpperCase() || "C"}
                  </div>

                  <span className="job-status">ACTIVE</span>
                </div>

                <div className="job-main">
                  <h3>{job.title}</h3>

                  <p className="company-name">
                    {job.company_name}
                  </p>

                  <p className="job-location">
                    📍 {job.location || "Location not specified"}
                  </p>

                  <p className="job-description">
                    {job.description}
                  </p>

                  <div className="job-meta">
                    {job.experience && (
                      <span>{job.experience}</span>
                    )}

                    {job.employment_type && (
                      <span>{job.employment_type}</span>
                    )}

                    {job.salary && (
                      <span>{job.salary}</span>
                    )}
                  </div>

                  {job.skills?.length > 0 && (
                    <div className="skills-list">
                      {job.skills.map((skill) => (
                        <span key={skill}>{skill}</span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="job-card-footer">
                  <span className="posted-date">
                    Posted recently
                  </span>

                  <button
                    className="view-job-button"
                    onClick={() => navigate(`/jobs/${job.id}`)}
                  >
                    View Job →
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default BrowseJobs;
