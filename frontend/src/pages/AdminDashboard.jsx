import { useEffect, useState } from "react";
import API from "../services/api";
import "./AdminDashboard.css";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [analyticsResponse, usersResponse] =
        await Promise.all([
          API.get("/admin/analytics"),
          API.get("/admin/users"),
        ]);

      setData(analyticsResponse.data);
      setUsers(usersResponse.data.users || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load admin dashboard."
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="admin-page">
        <div className="admin-loading">
          Loading platform analytics...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-page">
        <div className="admin-error">
          <h2>Admin Dashboard</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const overview = data.overview;
  const status = data.applications_by_status || {};

  return (
    <div className="admin-page">
      <div className="admin-header">
        <div>
          <span className="admin-label">
            PLATFORM ADMINISTRATION
          </span>

          <h1>Admin Dashboard</h1>

          <p>
            Monitor users, jobs, applications and hiring
            activity across the recruitment platform.
          </p>
        </div>

        <div className="admin-profile">
          <strong>{data.admin.name}</strong>
          <span>{data.admin.email}</span>
        </div>
      </div>

      <section className="admin-stat-grid">
        <div className="admin-stat-card">
          <span>Total Users</span>
          <strong>{overview.total_users}</strong>
          <small>
            +{data.last_7_days.new_users} this week
          </small>
        </div>

        <div className="admin-stat-card">
          <span>Candidates</span>
          <strong>{overview.total_candidates}</strong>
          <small>Job seekers</small>
        </div>

        <div className="admin-stat-card">
          <span>Employers</span>
          <strong>{overview.total_employers}</strong>
          <small>Hiring users</small>
        </div>

        <div className="admin-stat-card">
          <span>Companies</span>
          <strong>{overview.total_companies}</strong>
          <small>Registered companies</small>
        </div>

        <div className="admin-stat-card">
          <span>Total Jobs</span>
          <strong>{overview.total_jobs}</strong>
          <small>
            +{data.last_7_days.new_jobs} this week
          </small>
        </div>

        <div className="admin-stat-card">
          <span>Active Jobs</span>
          <strong>{overview.active_jobs}</strong>
          <small>Currently published</small>
        </div>

        <div className="admin-stat-card">
          <span>Applications</span>
          <strong>{overview.total_applications}</strong>
          <small>
            +{data.last_7_days.new_applications} this week
          </small>
        </div>

        <div className="admin-stat-card">
          <span>Closed Jobs</span>
          <strong>{overview.closed_jobs}</strong>
          <small>Completed postings</small>
        </div>
      </section>

      <div className="admin-main-grid">
        <section className="admin-panel">
          <div className="admin-panel-header">
            <div>
              <span>HIRING PIPELINE</span>
              <h2>Applications by Status</h2>
            </div>
          </div>

          <div className="admin-status-grid">
            {[
              "APPLIED",
              "SCREENING",
              "SHORTLISTED",
              "INTERVIEW",
              "OFFER",
              "HIRED",
              "REJECTED",
            ].map((item) => (
              <div
                className="admin-status-card"
                key={item}
              >
                <span>{item}</span>
                <strong>{status[item] || 0}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="admin-panel">
          <div className="admin-panel-header">
            <div>
              <span>PLATFORM USERS</span>
              <h2>Recent Users</h2>
            </div>
          </div>

          <div className="admin-users">
            {users.slice(0, 8).map((user) => (
              <div
                className="admin-user-row"
                key={user.id}
              >
                <div className="admin-user-avatar">
                  {user.name
                    ?.charAt(0)
                    ?.toUpperCase()}
                </div>

                <div>
                  <strong>{user.name}</strong>
                  <span>{user.email}</span>
                </div>

                <small>{user.role}</small>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="admin-panel recent-panel">
        <div className="admin-panel-header">
          <div>
            <span>RECENT ACTIVITY</span>
            <h2>Latest Applications</h2>
          </div>
        </div>

        {data.recent_applications.length === 0 ? (
          <div className="admin-empty">
            No applications yet.
          </div>
        ) : (
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>Job</th>
                  <th>Company</th>
                  <th>AI Fit</th>
                  <th>Status</th>
                  <th>Applied</th>
                </tr>
              </thead>

              <tbody>
                {data.recent_applications.map(
                  (application) => (
                    <tr
                      key={application.application_id}
                    >
                      <td>
                        {application.candidate_name}
                      </td>

                      <td>
                        {application.job_title}
                      </td>

                      <td>
                        {application.company_name}
                      </td>

                      <td>
                        {application.match_score !==
                        null
                          ? `${application.match_score}%`
                          : "—"}
                      </td>

                      <td>
                        <span className="admin-status-pill">
                          {application.status}
                        </span>
                      </td>

                      <td>
                        {new Date(
                          application.applied_at
                        ).toLocaleDateString()}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
