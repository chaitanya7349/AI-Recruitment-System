import { useEffect, useState } from "react";
import API from "../services/api";
import {
  FaUsers,
  FaBriefcase,
  FaStar,
} from "react-icons/fa";

function Dashboard() {
  const [stats, setStats] = useState({
    candidates: 0,
    jobs: 0,
    avgScore: 0,
  });

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await API.get("/employer/candidates");

      const candidates = response.data.candidates || [];

      let total = 0;

      candidates.forEach((c) => {
        total += c.score;
      });

      const avg =
        candidates.length > 0
          ? Math.round(total / candidates.length)
          : 0;

      setStats({
        candidates: candidates.length,
        jobs: 1,
        avgScore: avg,
      });
    } catch (err) {
      console.log(err);
    }
  };

  const cardStyle = {
    background: "white",
    borderRadius: "15px",
    padding: "25px",
    boxShadow: "0 8px 20px rgba(0,0,0,0.08)",
    flex: 1,
    minWidth: "220px",
    textAlign: "center",
  };

  return (
    <div
      style={{
        background: "#f4f6f9",
        minHeight: "100vh",
        padding: "30px",
      }}
    >
      <h1>Recruiter Dashboard</h1>

      <p
        style={{
          color: "#666",
          marginBottom: "30px",
        }}
      >
        AI Recruitment System Analytics
      </p>

      <div
        style={{
          display: "flex",
          gap: "25px",
          flexWrap: "wrap",
        }}
      >
        <div style={cardStyle}>
          <FaUsers size={40} color="#2563eb" />
          <h2>{stats.candidates}</h2>
          <p>Total Candidates</p>
        </div>

        <div style={cardStyle}>
          <FaBriefcase size={40} color="#16a34a" />
          <h2>{stats.jobs}</h2>
          <p>Jobs Uploaded</p>
        </div>

        <div style={cardStyle}>
          <FaStar size={40} color="#f59e0b" />
          <h2>{stats.avgScore}%</h2>
          <p>Average Score</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;