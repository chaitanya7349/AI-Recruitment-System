from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Table,
)

from sqlalchemy.orm import relationship

from .database import Base


# ---------------------------------------------------------
# USER <-> ROLE FOUNDATION
# ---------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    candidate_profile = relationship(
        "CandidateProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    employer_profile = relationship(
        "EmployerUser",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------
# COMPANY
# ---------------------------------------------------------

class Company(Base):
    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    description = Column(Text)

    website = Column(String(500))

    location = Column(String(200))

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    employers = relationship(
        "EmployerUser",
        back_populates="company",
    )

    jobs = relationship(
        "Job",
        back_populates="company",
    )


# ---------------------------------------------------------
# CANDIDATE PROFILE
# ---------------------------------------------------------

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    phone = Column(String(30))

    location = Column(String(200))

    bio = Column(Text)

    experience = Column(Text)

    education = Column(Text)

    user = relationship(
        "User",
        back_populates="candidate_profile",
    )

    resumes = relationship(
        "Resume",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    applications = relationship(
        "Application",
        back_populates="candidate",
    )


# ---------------------------------------------------------
# EMPLOYER USER
# ---------------------------------------------------------

class EmployerUser(Base):
    __tablename__ = "employer_users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
    )

    designation = Column(String(100))

    role_in_company = Column(String(50))

    user = relationship(
        "User",
        back_populates="employer_profile",
    )

    company = relationship(
        "Company",
        back_populates="employers",
    )

    jobs = relationship(
        "Job",
        back_populates="employer",
    )


# ---------------------------------------------------------
# RESUME
# ---------------------------------------------------------

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    original_filename = Column(
        String(255),
        nullable=False,
    )

    stored_filename = Column(
        String(255),
        nullable=False,
    )

    file_path = Column(
        String(500),
        nullable=False,
    )

    extracted_text = Column(Text)

    status = Column(
        String(50),
        default="Uploaded",
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    candidate = relationship(
        "CandidateProfile",
        back_populates="resumes",
    )


# ---------------------------------------------------------
# SKILLS
# ---------------------------------------------------------

class Skill(Base):
    __tablename__ = "skills"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    jobs = relationship(
        "Job",
        secondary="job_skills",
        back_populates="skills",
    )


# ---------------------------------------------------------
# JOB
# ---------------------------------------------------------

class Job(Base):
    __tablename__ = "jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
    )

    employer_id = Column(
        Integer,
        ForeignKey("employer_users.id"),
        nullable=False,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    location = Column(String(200))

    salary = Column(String(100))

    experience = Column(String(100))

    employment_type = Column(String(50))

    status = Column(
        String(30),
        default="ACTIVE",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    company = relationship(
        "Company",
        back_populates="jobs",
    )

    employer = relationship(
        "EmployerUser",
        back_populates="jobs",
    )

    skills = relationship(
        "Skill",
        secondary="job_skills",
        back_populates="jobs",
    )

    applications = relationship(
        "Application",
        back_populates="job",
    )


# ---------------------------------------------------------
# JOB <-> SKILL
# ---------------------------------------------------------

job_skills = Table(
    "job_skills",
    Base.metadata,

    Column(
        "job_id",
        ForeignKey("jobs.id"),
        primary_key=True,
    ),

    Column(
        "skill_id",
        ForeignKey("skills.id"),
        primary_key=True,
    ),
)


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

class Application(Base):
    __tablename__ = "applications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False,
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    resume_id = Column(
        Integer,
        ForeignKey("resumes.id"),
    )

    match_score = Column(Integer)

    status = Column(
        String(50),
        default="APPLIED",
    )

    applied_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    job = relationship(
        "Job",
        back_populates="applications",
    )

    candidate = relationship(
        "CandidateProfile",
        back_populates="applications",
    )

    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.changed_at",
    )


# ---------------------------------------------------------
# APPLICATION STATUS HISTORY
# ---------------------------------------------------------

class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=False,
        index=True,
    )

    old_status = Column(
        String(50),
    )

    new_status = Column(
        String(50),
        nullable=False,
    )

    feedback = Column(Text)

    changed_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
    )

    changed_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    application = relationship(
        "Application",
        back_populates="status_history",
    )

    changed_by = relationship(
        "User",
    )


# ---------------------------------------------------------
# SAVED JOBS
# ---------------------------------------------------------

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


# ---------------------------------------------------------
# NOTIFICATIONS
# ---------------------------------------------------------

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    is_read = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class TalentPoolEntry(Base):
    __tablename__ = "talent_pool"

    id = Column(Integer, primary_key=True, index=True)

    employer_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    candidate_id = Column(
        Integer,
        ForeignKey("candidate_profiles.id"),
        nullable=False,
        index=True,
    )

    source_application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=True,
        index=True,
    )

    notes = Column(Text, nullable=True)

    added_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    employer_user = relationship("User")

    candidate = relationship("CandidateProfile")

    source_application = relationship("Application")

class NotificationItem(Base):
    __tablename__ = "notification_items"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    application_id = Column(
        Integer,
        ForeignKey("applications.id"),
        nullable=True,
        index=True,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    notification_type = Column(
        String(50),
        nullable=False,
        default="GENERAL",
    )

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True,
    )

    user = relationship("User")

    application = relationship("Application")

