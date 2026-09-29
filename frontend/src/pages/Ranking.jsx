import { useEffect, useState } from "react";
import API from "../services/api";

function Ranking() {
  const [ranking, setRanking] = useState([]);

  useEffect(() => {
    loadRanking();
  }, []);

  const loadRanking = async () => {
  try {
    const skills = JSON.parse(localStorage.getItem("jobSkills")) || [];

    const response = await API.post("/employer/rank-candidates", {
      skills: skills,
    });

    setRanking(response.data.ranking);
  } catch (error) {
    console.error(error);
  }
};

  return (
  <div
    style={{
      padding: "40px",
      background: "#f4f6f9",
      minHeight: "100vh",
      fontFamily: "Arial",
    }}
  >
    <h1
      style={{
        textAlign: "center",
        marginBottom: "35px",
      }}
    >
      🏆 Candidate Ranking
    </h1>

    {ranking.length === 0 ? (
      <h3 style={{ textAlign: "center" }}>
        No ranked candidates found.
      </h3>
    ) : (
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          background: "#fff",
          boxShadow: "0 5px 20px rgba(0,0,0,0.1)",
          borderRadius: "12px",
          overflow: "hidden",
        }}
      >
        <thead
          style={{
            background: "#2563eb",
            color: "white",
          }}
        >
          <tr>
            <th style={{ padding: "15px" }}>Rank</th>
            <th>Name</th>
            <th>Email</th>
            <th>Resume Score</th>
            <th>Job Match</th>
            <th>Final Score</th>
          </tr>
        </thead>

        <tbody>
          {ranking.map((candidate, index) => (
            <tr
              key={index}
              style={{
                textAlign: "center",
                borderBottom: "1px solid #eee",
              }}
            >
              <td style={{ fontSize: "22px" }}>
                {candidate.rank === 1
                  ? "🥇"
                  : candidate.rank === 2
                  ? "🥈"
                  : candidate.rank === 3
                  ? "🥉"
                  : candidate.rank}
              </td>

              <td>{candidate.name}</td>

              <td>{candidate.email}</td>

              <td>{candidate.resume_score}%</td>

              <td>{candidate.job_match}%</td>

              <td style={{ width: "220px" }}>
                <div
                  style={{
                    width: "150px",
                    height: "10px",
                    background: "#ddd",
                    borderRadius: "20px",
                    margin: "auto",
                  }}
                >
                  <div
                    style={{
                      width: `${candidate.final_score}%`,
                      height: "10px",
                      background: "#22c55e",
                      borderRadius: "20px",
                    }}
                  ></div>
                </div>

                <div style={{ marginTop: "6px" }}>
                  <strong>{candidate.final_score}%</strong>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    )}
  </div>
);
}

export default Ranking;