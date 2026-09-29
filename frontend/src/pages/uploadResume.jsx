import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";

function UploadResume() {
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setFile(selectedFile || null);
    setMessage("");
    setError("");
  };

  const uploadResume = async (event) => {
    event.preventDefault();

    if (!file) {
      setError("Please select a PDF or DOCX resume.");
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowedTypes.includes(file.type)) {
      setError("Only PDF and DOCX files are supported.");
      return;
    }

    const formData = new FormData();

    formData.append("file", file);

    try {
      setUploading(true);
      setMessage("");
      setError("");

      const response = await API.post(
        "/upload-resume",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setMessage(
        response.data.message ||
        "Resume uploaded successfully."
      );

    } catch (err) {
      console.error(err);

      if (err.response?.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        navigate("/login");
        return;
      }

      setError(
        err.response?.data?.detail ||
        "Unable to upload resume."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f6f7fb",
        padding: "50px",
      }}
    >

      <div
        style={{
          maxWidth: "700px",
          margin: "0 auto",
          background: "white",
          padding: "35px",
          borderRadius: "18px",
          border: "1px solid #e5e7ed",
        }}
      >

        <button
          onClick={() =>
            navigate("/candidate-dashboard")
          }
          style={{
            border: 0,
            background: "transparent",
            color: "#6258e8",
            fontWeight: 700,
            cursor: "pointer",
            marginBottom: "25px",
          }}
        >
          ← Back to Dashboard
        </button>

        <h1>Upload Resume</h1>

        <p style={{ color: "#697386" }}>
          Upload your resume to enable resume parsing
          and AI-powered career analysis.
        </p>

        <form onSubmit={uploadResume}>

          <div
            style={{
              marginTop: "30px",
              border: "2px dashed #dfe2e9",
              borderRadius: "14px",
              padding: "45px 25px",
              textAlign: "center",
            }}
          >

            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
            />

            {file && (
              <p
                style={{
                  marginTop: "15px",
                  color: "#4d5668",
                }}
              >
                Selected: <strong>{file.name}</strong>
              </p>
            )}

          </div>

          {error && (
            <div
              style={{
                marginTop: "20px",
                padding: "13px",
                borderRadius: "9px",
                background: "#fff0f0",
                color: "#c62828",
              }}
            >
              {error}
            </div>
          )}

          {message && (
            <div
              style={{
                marginTop: "20px",
                padding: "13px",
                borderRadius: "9px",
                background: "#e8f8ef",
                color: "#18794e",
              }}
            >
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={uploading}
            style={{
              marginTop: "25px",
              border: 0,
              background: "#6258e8",
              color: "white",
              padding: "13px 22px",
              borderRadius: "10px",
              fontWeight: 800,
              cursor: uploading
                ? "not-allowed"
                : "pointer",
              opacity: uploading ? 0.6 : 1,
            }}
          >
            {uploading
              ? "Uploading..."
              : "Upload Resume"}
          </button>

        </form>

      </div>

    </div>
  );
}

export default UploadResume;
