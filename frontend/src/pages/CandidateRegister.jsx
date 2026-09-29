import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./CandidateRegister.css";

function CandidateRegister() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const register = async (event) => {
    event.preventDefault();

    setMessage("");
    setError("");

    try {
      setLoading(true);

      await API.post(
        "/candidate/register",
        form
      );

      setMessage(
        "Account created successfully. Redirecting to login..."
      );

      setTimeout(() => {
        navigate("/login");
      }, 1200);

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to create account."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="candidate-register-page">

      <div className="candidate-register-card">

        <div className="candidate-register-brand">
          NEXORA
        </div>

        <h1>Create your account</h1>

        <p>
          Build your profile and discover jobs that
          match your skills.
        </p>

        <form onSubmit={register}>

          <label>
            Full Name
          </label>

          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Your full name"
            required
          />

          <label>
            Email Address
          </label>

          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />

          <label>
            Password
          </label>

          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            placeholder="Create a password"
            required
          />

          {error && (
            <div className="register-error">
              {error}
            </div>
          )}

          {message && (
            <div className="register-success">
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Creating account..."
              : "Create Account"}
          </button>

        </form>

        <button
          className="back-login"
          onClick={() => navigate("/login")}
        >
          Already have an account? Sign in
        </button>

      </div>

    </div>
  );
}

export default CandidateRegister;
