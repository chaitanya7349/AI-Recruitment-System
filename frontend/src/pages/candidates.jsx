import { useEffect, useState } from "react";
import API from "../services/api";
import { FaSearch, FaUserGraduate } from "react-icons/fa";
import { Link } from "react-router-dom";

function Candidates() {
  const [candidates, setCandidates] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      const res = await API.get("/employer/candidates");
      setCandidates(res.data.candidates);
    } catch (err) {
      console.log(err);
    }
  };

  const filteredCandidates = candidates.filter(
    (candidate) =>
      candidate.name.toLowerCase().includes(search.toLowerCase()) ||
      candidate.email.toLowerCase().includes(search.toLowerCase())
  );

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
        marginBottom: "30px",
      }}
    >
      <FaUserGraduate color="#2563eb" /> Candidates
    </h1>

    <div
      style={{
        display: "flex",
        justifyContent: "center",
        marginBottom: "30px",
      }}
    >
      <div style={{ position: "relative", width: "400px" }}>
        <FaSearch
          style={{
            position: "absolute",
            top: "13px",
            left: "12px",
            color: "#888",
          }}
        />

        <input
          type="text"
          placeholder="Search Candidate..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: "100%",
            padding: "12px 12px 12px 38px",
            borderRadius: "10px",
            border: "1px solid #ddd",
            outline: "none",
          }}
        />
      </div>
    </div>

    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit,minmax(350px,1fr))",
        gap: "25px",
      }}
    >
      {filteredCandidates.map((candidate) => (
        <div
          key={candidate.resume_id}
          style={{
            background: "white",
            borderRadius: "15px",
            padding: "25px",
            boxShadow: "0 8px 20px rgba(0,0,0,0.08)",
          }}
        >
          <h2>{candidate.name}</h2>

          <p>📧 {candidate.email}</p>

          <p>📞 {candidate.phone}</p>

          <p>
            <strong>Score:</strong> {candidate.score}%
          </p>

          <div
            style={{
              width: "100%",
              height: "10px",
              background: "#ddd",
              borderRadius: "20px",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                width: `${candidate.score}%`,
                height: "10px",
                background: "#22c55e",
                borderRadius: "20px",
              }}
            />
          </div>

          <h4>Skills</h4>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              marginBottom: "20px",
            }}
          >
            {candidate.skills.slice(0, 6).map((skill, index) => (
              <span
                key={index}
                style={{
                  background: "#2563eb",
                  color: "white",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  fontSize: "13px",
                }}
              >
                {skill}
              </span>
            ))}

            {candidate.skills.length > 6 && (
              <span
                style={{
                  background: "#e5e7eb",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  fontSize: "13px",
                }}
              >
                +{candidate.skills.length - 6} more
              </span>
            )}
          </div>

          <Link
            to={`/candidate/${candidate.resume_id}`}
            style={{
              display: "inline-block",
              background: "#2563eb",
              color: "white",
              padding: "10px 20px",
              borderRadius: "8px",
              textDecoration: "none",
            }}
          >
            View Profile
          </Link>
        </div>
      ))}
    </div>
  </div>
);
}

export default Candidates;