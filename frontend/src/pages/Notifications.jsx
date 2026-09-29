import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./Notifications.css";

export default function Notifications() {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await API.get("/notifications/");

      setNotifications(
        response.data.notifications || []
      );

      setUnreadCount(
        response.data.unread_count || 0
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load notifications."
      );
    } finally {
      setLoading(false);
    }
  };

  const markRead = async (notification) => {
    if (notification.is_read) {
      openNotification(notification);
      return;
    }

    try {
      await API.patch(
        `/notifications/${notification.id}/read`
      );

      setNotifications((current) =>
        current.map((item) =>
          item.id === notification.id
            ? { ...item, is_read: true }
            : item
        )
      );

      setUnreadCount((count) =>
        Math.max(0, count - 1)
      );

      openNotification(notification);
    } catch {
      openNotification(notification);
    }
  };

  const openNotification = (notification) => {
    if (notification.application_id) {
      const user = JSON.parse(
        localStorage.getItem("user") || "null"
      );

      if (user?.role === "EMPLOYER_USER") {
        navigate(
          `/employer/applicants/${notification.application_id}`
        );
      } else if (user?.role === "JOB_SEEKER") {
        navigate("/candidate-dashboard");
      }
    }
  };

  const markAllRead = async () => {
    try {
      await API.patch("/notifications/read-all");

      setNotifications((current) =>
        current.map((item) => ({
          ...item,
          is_read: true,
        }))
      );

      setUnreadCount(0);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to mark notifications as read."
      );
    }
  };

  if (loading) {
    return (
      <div className="notifications-page">
        <div className="notifications-loading">
          Loading notifications...
        </div>
      </div>
    );
  }

  return (
    <div className="notifications-page">
      <div className="notifications-header">
        <div>
          <span>ACTIVITY CENTER</span>

          <h1>Notifications</h1>

          <p>
            Stay informed about applications and hiring
            activity connected to your account.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            className="mark-all-button"
            onClick={markAllRead}
          >
            Mark all as read
          </button>
        )}
      </div>

      {error && (
        <div className="notifications-error">
          {error}
        </div>
      )}

      {notifications.length === 0 ? (
        <div className="notifications-empty">
          <div>✓</div>
          <h2>No notifications yet</h2>
          <p>
            Important application and hiring activity will
            appear here.
          </p>
        </div>
      ) : (
        <div className="notification-list">
          {notifications.map((notification) => (
            <button
              key={notification.id}
              className={`notification-card ${
                notification.is_read
                  ? "read"
                  : "unread"
              }`}
              onClick={() =>
                markRead(notification)
              }
            >
              <div className="notification-icon">
                {notification.notification_type ===
                "APPLICATION"
                  ? "A"
                  : "!"
                }
              </div>

              <div className="notification-content">
                <div className="notification-title-row">
                  <h2>{notification.title}</h2>

                  {!notification.is_read && (
                    <span className="unread-dot" />
                  )}
                </div>

                <p>{notification.message}</p>

                <small>
                  {new Date(
                    notification.created_at
                  ).toLocaleString()}
                </small>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
