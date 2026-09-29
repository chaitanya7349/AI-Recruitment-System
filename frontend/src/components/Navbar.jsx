import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import API from "../services/api";
import "./Navbar.css";

export default function Navbar() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadUser();
  }, []);

  useEffect(() => {
    if (user) {
      loadUnreadNotifications();

      const interval = setInterval(() => {
        loadUnreadNotifications();
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [user]);

  const loadUser = () => {
    try {
      const storedUser = localStorage.getItem("user");

      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    } catch {
      setUser(null);
    }
  };

  const loadUnreadNotifications = async () => {
    try {
      const response = await API.get("/notifications/");

      setUnreadCount(
        response.data.unread_count || 0
      );
    } catch {
      setUnreadCount(0);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    setUser(null);
    setUnreadCount(0);

    navigate("/login");
  };

  return (
    <nav className="main-navbar">
      <Link to="/" className="navbar-brand">
        <span className="navbar-brand-mark">
          AI
        </span>

        <span>
          Recruitment
        </span>
      </Link>

      <div className="navbar-links">
        <Link to="/">Home</Link>

        <Link to="/jobs">
          Browse Jobs
        </Link>

        {user?.role === "JOB_SEEKER" && (
          <Link to="/candidate-dashboard">
            Dashboard
          </Link>
        )}

        {user?.role === "EMPLOYER_USER" && (
          <Link to="/employer">
            Employer Dashboard
          </Link>
        )}

        {user?.role === "ADMIN" && (
          <Link to="/dashboard">
            Admin Dashboard
          </Link>
        )}
      </div>

      <div className="navbar-actions">
        {user && (
          <button
            className="notification-bell"
            onClick={() =>
              navigate("/notifications")
            }
            aria-label="Notifications"
            title="Notifications"
          >
            <span className="bell-symbol">
              🔔
            </span>

            {unreadCount > 0 && (
              <span className="notification-badge">
                {unreadCount > 99
                  ? "99+"
                  : unreadCount}
              </span>
            )}
          </button>
        )}

        {!user ? (
          <>
            <Link
              to="/login"
              className="navbar-login"
            >
              Login
            </Link>

            <Link
              to="/register"
              className="navbar-register"
            >
              Register
            </Link>
          </>
        ) : (
          <div className="navbar-user-area">
            <span className="navbar-user-name">
              {user.name}
            </span>

            <button
              className="navbar-logout"
              onClick={logout}
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
