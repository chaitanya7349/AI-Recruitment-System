import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";
import "./Login.css";
function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const login = async (event) => {
    event.preventDefault();

    setMessage("");

    if (!email || !password) {
      setMessage("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);

      const response = await API.post("/login", {
        email,
        password,
      });

      const {
        access_token,
        user,
      } = response.data;

      // Store authentication token
      localStorage.setItem(
        "token",
        access_token
      );

      // Store logged-in user information
      localStorage.setItem(
        "user",
        JSON.stringify(user)
      );

      // Redirect according to the user's role
      if (user.role === "EMPLOYER_USER") {
  navigate("/employer");
} else if (user.role === "JOB_SEEKER") {
  navigate("/candidate-dashboard");
} else if (user.role === "ADMIN") {
  navigate("/dashboard");
} else {
  navigate("/dashboard");
}
    } catch (error) {
      console.error("Login error:", error);

      const backendMessage =
        error.response?.data?.detail;

      setMessage(
        backendMessage ||
        "Unable to login. Please check your credentials."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">

      <div className="login-card">

        <div className="login-brand">
          NEXORA
        </div>

        <h1>
          Welcome back
        </h1>

        <p className="login-subtitle">
          Sign in to continue to your career and hiring platform.
        </p>

        <form onSubmit={login}>

          <div className="login-field">

            <label>
              Email address
            </label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              autoComplete="email"
            />

          </div>

          <div className="login-field">

            <label>
              Password
            </label>

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              autoComplete="current-password"
            />

          </div>

          {message && (
            <div className="login-error">
              {message}
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

        </form>

        <div className="login-divider">
          <span>OR</span>
        </div>

        <div className="login-links">

          <button
            type="button"
            onClick={() => navigate("/register")}
          >
            Create a Job Seeker account
          </button>

          <button
            type="button"
            onClick={() => navigate("/employer")}
          >
            I'm an Employer
          </button>

        </div>

        <p className="login-footer">
          AI-powered career and hiring intelligence
        </p>

      </div>

    </div>
  );
}

export default Login;
