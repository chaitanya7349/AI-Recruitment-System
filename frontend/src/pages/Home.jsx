import { Link } from "react-router-dom";
import {
  FaSearch,
  FaMapMarkerAlt,
  FaBrain,
  FaChartLine,
  FaFileAlt,
  FaBuilding,
  FaArrowRight,
  FaCheckCircle,
} from "react-icons/fa";
import "./Home.css";

function Home() {
  return (
    <div className="home-page">

      {/* ================= NAVBAR ================= */}

      <nav className="home-navbar">
        <Link to="/" className="brand">
          <span className="brand-mark">N</span>
          <span>NEXORA</span>
        </Link>

        <div className="nav-links">
          <Link to="/jobs">Jobs</Link>
          <Link to="/companies">Companies</Link>
          <Link to="/career-fit">Career Intelligence</Link>
          <Link to="/employer">For Employers</Link>
        </div>

        <div className="nav-actions">
          <Link to="/login" className="login-link">
            Login
          </Link>

          <Link to="/register" className="signup-button">
            Get Started
          </Link>
        </div>
      </nav>

      {/* ================= HERO ================= */}

      <section className="hero-section">

        <div className="hero-content">

          <div className="hero-badge">
            <FaBrain />
            AI-powered career intelligence
          </div>

          <h1>
            Find work that
            <span> fits you.</span>
          </h1>

          <p className="hero-description">
            Discover opportunities based on your skills, experience and
            career goals — then understand exactly why a job fits you.
          </p>

          {/* SEARCH */}

          <div className="job-search">

            <div className="search-field">
              <FaSearch />
              <input
                type="text"
                placeholder="Job title, skills or company"
              />
            </div>

            <div className="search-field location-field">
              <FaMapMarkerAlt />
              <input
                type="text"
                placeholder="Location"
              />
            </div>

            <Link to="/jobs" className="search-button">
              Find Jobs
              <FaArrowRight />
            </Link>

          </div>

          <div className="popular-searches">
            <span>Popular:</span>

            <Link to="/jobs?search=Python">
              Python Developer
            </Link>

            <Link to="/jobs?search=Data Analyst">
              Data Analyst
            </Link>

            <Link to="/jobs?search=Machine Learning">
              Machine Learning
            </Link>

            <Link to="/jobs?search=Java">
              Java Developer
            </Link>
          </div>

        </div>

        {/* HERO INTELLIGENCE CARD */}

        <div className="hero-visual">

          <div className="fit-card">

            <div className="fit-card-header">
              <div>
                <small>CAREER FIT</small>
                <h3>Python Backend Developer</h3>
              </div>

              <div className="fit-score">
                84%
              </div>
            </div>

            <div className="fit-progress">
              <div className="fit-progress-bar"></div>
            </div>

            <div className="fit-section">

              <div className="fit-title">
                <span>Strong matches</span>
                <span>4</span>
              </div>

              <div className="skill-row">
                <FaCheckCircle />
                Python
              </div>

              <div className="skill-row">
                <FaCheckCircle />
                FastAPI
              </div>

              <div className="skill-row">
                <FaCheckCircle />
                PostgreSQL
              </div>

              <div className="skill-row">
                <FaCheckCircle />
                REST APIs
              </div>

            </div>

            <div className="fit-gap">

              <div className="fit-title">
                <span>Skills to improve</span>
                <span>2</span>
              </div>

              <div className="gap-row">
                Docker
              </div>

              <div className="gap-row">
                AWS
              </div>

            </div>

            <button className="fit-report-button">
              View Fit Report
              <FaArrowRight />
            </button>

          </div>

        </div>

      </section>

      {/* ================= TRUST / VALUE ================= */}

      <section className="value-section">

        <div className="value-item">
          <FaBrain />
          <div>
            <h3>AI Career Fit</h3>
            <p>
              Understand how closely your profile matches a job.
            </p>
          </div>
        </div>

        <div className="value-item">
          <FaChartLine />
          <div>
            <h3>Skill Gap Analysis</h3>
            <p>
              Discover what skills you need to improve.
            </p>
          </div>
        </div>

        <div className="value-item">
          <FaFileAlt />
          <div>
            <h3>Explainable Results</h3>
            <p>
              See why the platform recommends an opportunity.
            </p>
          </div>
        </div>

      </section>

      {/* ================= HOW IT WORKS ================= */}

      <section className="how-section">

        <div className="section-heading">
          <span>HOW IT WORKS</span>

          <h2>
            More than a job search.
          </h2>

          <p>
            NEXORA connects job discovery with career intelligence.
          </p>
        </div>

        <div className="steps">

          <div className="step-card">

            <div className="step-number">
              01
            </div>

            <FaFileAlt className="step-icon" />

            <h3>
              Build your profile
            </h3>

            <p>
              Upload your resume and let our AI understand your
              skills, education, experience and projects.
            </p>

          </div>

          <div className="step-card">

            <div className="step-number">
              02
            </div>

            <FaSearch className="step-icon" />

            <h3>
              Discover opportunities
            </h3>

            <p>
              Search jobs and discover opportunities that match
              your professional profile.
            </p>

          </div>

          <div className="step-card">

            <div className="step-number">
              03
            </div>

            <FaBrain className="step-icon" />

            <h3>
              Understand your fit
            </h3>

            <p>
              See matching skills, missing skills and your
              career-readiness for each opportunity.
            </p>

          </div>

          <div className="step-card">

            <div className="step-number">
              04
            </div>

            <FaChartLine className="step-icon" />

            <h3>
              Grow and apply
            </h3>

            <p>
              Improve your skill gaps, apply with confidence and
              track your career journey.
            </p>

          </div>

        </div>

      </section>

      {/* ================= CAREER INTELLIGENCE ================= */}

      <section className="intelligence-section">

        <div className="intelligence-content">

          <span className="section-label">
            CAREER INTELLIGENCE
          </span>

          <h2>
            Don't just ask
            <span> "Can I get this job?"</span>
          </h2>

          <p>
            Understand where you stand today and what you need
            to become a stronger candidate tomorrow.
          </p>

          <div className="intelligence-list">

            <div>
              <FaCheckCircle />
              Skills you already have
            </div>

            <div>
              <FaCheckCircle />
              Skills the job requires
            </div>

            <div>
              <FaCheckCircle />
              Missing or weak skills
            </div>

            <div>
              <FaCheckCircle />
              Recommended improvement areas
            </div>

          </div>

          <Link to="/career-fit" className="primary-button">
            Explore Career Intelligence
            <FaArrowRight />
          </Link>

        </div>

        <div className="readiness-card">

          <div className="readiness-header">
            <div>
              <small>YOUR READINESS</small>
              <h3>Machine Learning Engineer</h3>
            </div>

            <strong>78%</strong>
          </div>

          <div className="readiness-bar">
            <div></div>
          </div>

          <p>
            You're close to being ready for this role.
          </p>

          <div className="recommendation">
            <strong>Recommended next steps</strong>

            <span>
              → Docker
            </span>

            <span>
              → AWS deployment
            </span>

            <span>
              → MLOps fundamentals
            </span>
          </div>

        </div>

      </section>

      {/* ================= EMPLOYERS ================= */}

      <section className="employer-section">

        <div className="employer-card">

          <div className="employer-icon">
            <FaBuilding />
          </div>

          <div className="employer-content">

            <span>
              FOR EMPLOYERS
            </span>

            <h2>
              Hire with evidence,
              not just keywords.
            </h2>

            <p>
              Create jobs, receive applications and use AI-powered
              candidate intelligence to understand skills,
              experience and fit.
            </p>

            <Link
              to="/employer"
              className="employer-button"
            >
              Explore Employer Platform
              <FaArrowRight />
            </Link>

          </div>

        </div>

      </section>

      {/* ================= FINAL CTA ================= */}

      <section className="final-cta">

        <h2>
          Your next opportunity
          starts here.
        </h2>

        <p>
          Find opportunities. Understand your fit. Build your career.
        </p>

        <div className="cta-buttons">

          <Link
            to="/jobs"
            className="primary-button"
          >
            Find a Job
            <FaArrowRight />
          </Link>

          <Link
            to="/employer"
            className="secondary-button"
          >
            Hire Talent
          </Link>

        </div>

      </section>

      {/* ================= FOOTER ================= */}

      <footer className="home-footer">

        <div className="footer-brand">
          <div className="brand">
            <span className="brand-mark">N</span>
            NEXORA
          </div>

          <p>
            AI Career & Hiring Intelligence
          </p>
        </div>

        <div className="footer-links">

          <div>
            <h4>Platform</h4>
            <Link to="/jobs">Jobs</Link>
            <Link to="/companies">Companies</Link>
            <Link to="/career-fit">
              Career Intelligence
            </Link>
          </div>

          <div>
            <h4>Employers</h4>
            <Link to="/employer">
              Hire Talent
            </Link>

            <Link to="/employer">
              Post a Job
            </Link>
          </div>

          <div>
            <h4>Account</h4>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </div>

        </div>

      </footer>

    </div>
  );
}

export default Home;
