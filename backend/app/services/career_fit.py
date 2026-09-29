import re


SKILL_ALIASES = {
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "rest": "rest api",
    "restful api": "rest api",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "python3": "python",
    "py": "python",
}


KNOWN_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",
    "php",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "fastapi",
    "django",
    "flask",
    "react",
    "angular",
    "vue",
    "node.js",
    "express",
    "rest api",
    "graphql",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "github",
    "linux",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "spark",
    "airflow",
    "machine learning",
    "deep learning",
    "data engineering",
    "data analysis",
]


def normalize_skill(skill):
    skill = skill.lower().strip()

    skill = re.sub(
        r"[^a-z0-9+#.\s]",
        " ",
        skill
    )

    skill = re.sub(
        r"\s+",
        " ",
        skill
    ).strip()

    return SKILL_ALIASES.get(
        skill,
        skill
    )


def extract_skills(text):
    if not text:
        return []

    text = text.lower()

    found = set()

    for skill in KNOWN_SKILLS:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"

        if re.search(pattern, text):
            found.add(
                normalize_skill(skill)
            )

    return sorted(found)


def calculate_career_fit(
    resume_text,
    job_title,
    job_description,
    required_skills
):
    resume_skills = set(
        extract_skills(resume_text)
    )

    job_text = " ".join([
        job_title or "",
        job_description or "",
        " ".join(required_skills or []),
    ])

    detected_job_skills = set(
        extract_skills(job_text)
    )

    explicit_job_skills = {
        normalize_skill(skill)
        for skill in (required_skills or [])
        if skill
    }

    job_skills = (
        detected_job_skills |
        explicit_job_skills
    )

    matching_skills = sorted(
        resume_skills & job_skills
    )

    missing_skills = sorted(
        job_skills - resume_skills
    )

    if not job_skills:
        score = 0
    else:
        score = round(
            (
                len(matching_skills)
                / len(job_skills)
            ) * 100
        )

    if score >= 80:
        readiness = "Strong Fit"
    elif score >= 60:
        readiness = "Good Potential"
    elif score >= 40:
        readiness = "Developing Fit"
    else:
        readiness = "Needs Improvement"

    recommendations = [
        f"Develop {skill} through a project or practical exercise."
        for skill in missing_skills[:5]
    ]

    return {
        "score": score,
        "readiness": readiness,
        "resume_skills": sorted(resume_skills),
        "job_skills": sorted(job_skills),
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendations,
    }
