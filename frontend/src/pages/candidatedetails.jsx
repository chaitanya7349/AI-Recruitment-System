import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";

function CandidateDetails() {
  const { id } = useParams();

  const [candidate, setCandidate] = useState(null);

  useEffect(() => {
    loadCandidate();
  }, []);

  const loadCandidate = async () => {
    try {
      const response = await API.get(`/employer/candidates/${id}`);

      const found = response.data.candidates.find(
        (c) => c.resume_id === Number(id)
      );

      setCandidate(found);
    } catch (error) {
      console.log(error);
    }
  };

  if (!candidate) {
    return (
      <div style={{ padding: "40px" }}>
        Loading Candidate...
      </div>
    );
  }

  return (
    <div
      style={{
        background: "#f4f6f9",
        minHeight: "100vh",
        padding: "40px",
      }}
    >
      <div
        style={{
          maxWidth: "800px",
          margin: "auto",
          background: "white",
          padding: "40px",
          borderRadius: "15px",
          boxShadow: "0 8px 20px rgba(0,0,0,0.1)",
        }}
      >
        <h1 style={{ textAlign: "center" }}>
          👤 Candidate Profile
        </h1>

        <hr />

        <p><strong>Name:</strong> {candidate.name}</p>

        <p><strong>Email:</strong> {candidate.email}</p>

        <p><strong>Phone:</strong> {candidate.phone}</p>

        <p><strong>Score:</strong> {candidate.score}%</p>

        <h3>Skills</h3>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          {candidate.skills.map((skill, index) => (
            <span
              key={index}
              style={{
                background: "#2563eb",
                color: "white",
                padding: "8px 15px",
                borderRadius: "20px",
              }}
            >
              {skill}
            </span>
          ))}
        </div>

        <h3 style={{ marginTop: "30px" }}>
          Education
        </h3>

        <ul>
          {candidate.education.map((edu, index) => (
            <li key={index}>{edu}</li>
          ))}
        </ul>

        <h3>Experience</h3>

        <p>{candidate.experience}</p>
      </div>
    </div>
  );
}

export default CandidateDetails;