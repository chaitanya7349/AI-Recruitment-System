import { Link, useLocation, useNavigate } from "react-router-dom";

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const user = JSON.parse(
    localStorage.getItem("user") || "null"
  );

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    navigate("/login", {
      replace: true,
    });
  };

  /*
   * The old recruiter navigation has been removed.
   *
   * The main application now has separate experiences:
   *
   * JOB SEEKER
   *   Candidate Dashboard
   *   Browse Jobs
   *   My Applications
   *   Career Fit
   *
   * EMPLOYER
   *   Employer Dashboard
   *   Jobs
   *   Applicants
   *
   * ADMIN
   *   Dashboard
   *
   * Employer and candidate pages normally do not display
   * this sidebar because App.jsx treats those pages as
   * full application pages.
   */

  const menu =
    user?.role === "ADMIN"
      ? [
          {
            name: "Admin Dashboard",
            path: "/dashboard",
          },
        ]
      : [
          {
            name: "Home",
            path: "/",
          },
          {
            name: "Browse Jobs",
            path: "/jobs",
          },
        ];

  return (
    <aside
      style={{
        width: "250px",
        height: "100vh",
        background: "#1e293b",
        color: "white",
        padding: "20px",
        position: "fixed",
        left: 0,
        top: 0,
        display: "flex",
        flexDirection: "column",
        boxSizing: "border-box",
        zIndex: 1000,
      }}
    >

      {/* BRAND */}

      <div
        style={{
          textAlign: "center",
          marginBottom: "40px",
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: "22px",
          }}
        >
          AI Recruitment
        </h2>

        <span
          style={{
            display: "block",
            marginTop: "6px",
            fontSize: "11px",
            opacity: 0.7,
            letterSpacing: "1px",
          }}
        >
          INTELLIGENCE PLATFORM
        </span>
      </div>

      {/* NAVIGATION */}

      <nav
        style={{
          flex: 1,
        }}
      >
        {menu.map((item) => {
          const active =
            location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: "block",
                padding: "15px",
                marginBottom: "10px",
                textDecoration: "none",
                color: "white",
                borderRadius: "8px",
                background: active
                  ? "#2563eb"
                  : "transparent",
                transition: "background 0.2s ease",
              }}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* CURRENT USER */}

      {user && (
        <div
          style={{
            borderTop: "1px solid rgba(255,255,255,0.15)",
            paddingTop: "15px",
            marginBottom: "15px",
          }}
        >
          <div
            style={{
              fontSize: "14px",
              fontWeight: "600",
            }}
          >
            {user.name}
          </div>

          <div
            style={{
              marginTop: "4px",
              fontSize: "11px",
              opacity: 0.7,
            }}
          >
            {user.role}
          </div>
        </div>
      )}

      {/* LOGOUT */}

      <button
        onClick={logout}
        style={{
          width: "100%",
          padding: "12px",
          background: "#dc2626",
          color: "white",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "16px",
          marginBottom: "10px",
        }}
      >
        Logout
      </button>

    </aside>
  );
}

export default Sidebar;
