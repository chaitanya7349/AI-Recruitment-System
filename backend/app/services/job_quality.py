import re


def analyze_job_quality(job_data: dict) -> dict:
    title = (job_data.get("title") or "").strip()
    description = (job_data.get("description") or "").strip()
    location = (job_data.get("location") or "").strip()
    salary = (job_data.get("salary") or "").strip()
    experience = (job_data.get("experience") or "").strip()
    employment_type = (job_data.get("employment_type") or "").strip()
    skills = job_data.get("skills") or []

    score = 0
    checks = []
    suggestions = []

    # Job title
    if title:
        if len(title) >= 5:
            score += 15
            checks.append({
                "name": "Job title",
                "status": "GOOD",
                "message": "The job has a clear title."
            })
        else:
            score += 7
            checks.append({
                "name": "Job title",
                "status": "NEEDS_IMPROVEMENT",
                "message": "The title is very short."
            })
            suggestions.append(
                "Use a specific role title such as 'Python Backend Developer'."
            )
    else:
        checks.append({
            "name": "Job title",
            "status": "MISSING",
            "message": "No job title was provided."
        })
        suggestions.append("Add a clear and specific job title.")

    # Description
    if description:
        word_count = len(re.findall(r"\b[\w+#.-]+\b", description))

        if word_count >= 100:
            score += 25
            checks.append({
                "name": "Job description",
                "status": "GOOD",
                "message": f"Description contains approximately {word_count} words."
            })
        elif word_count >= 50:
            score += 15
            checks.append({
                "name": "Job description",
                "status": "FAIR",
                "message": f"Description contains approximately {word_count} words."
            })
            suggestions.append(
                "Expand the description with responsibilities and role expectations."
            )
        else:
            score += 7
            checks.append({
                "name": "Job description",
                "status": "NEEDS_IMPROVEMENT",
                "message": "The job description is short."
            })
            suggestions.append(
                "Add responsibilities, expectations, qualifications and role context."
            )
    else:
        checks.append({
            "name": "Job description",
            "status": "MISSING",
            "message": "No job description was provided."
        })
        suggestions.append("Add a detailed job description.")

    # Skills
    clean_skills = [
        str(skill).strip()
        for skill in skills
        if str(skill).strip()
    ]

    if len(clean_skills) >= 5:
        score += 20
        checks.append({
            "name": "Required skills",
            "status": "GOOD",
            "message": f"{len(clean_skills)} skills were specified."
        })
    elif len(clean_skills) >= 2:
        score += 12
        checks.append({
            "name": "Required skills",
            "status": "FAIR",
            "message": f"{len(clean_skills)} skills were specified."
        })
        suggestions.append(
            "Consider adding the core technical or professional skills required."
        )
    else:
        score += 5
        checks.append({
            "name": "Required skills",
            "status": "NEEDS_IMPROVEMENT",
            "message": "Very few required skills were specified."
        })
        suggestions.append(
            "Add the most important skills needed to perform the role."
        )

    # Experience
    if experience:
        score += 10
        checks.append({
            "name": "Experience requirement",
            "status": "GOOD",
            "message": "Experience expectations are specified."
        })
    else:
        checks.append({
            "name": "Experience requirement",
            "status": "MISSING",
            "message": "No experience requirement was specified."
        })
        suggestions.append(
            "Specify the expected experience level."
        )

    # Location
    if location:
        score += 8
        checks.append({
            "name": "Location",
            "status": "GOOD",
            "message": "Job location is specified."
        })
    else:
        checks.append({
            "name": "Location",
            "status": "MISSING",
            "message": "No job location was specified."
        })
        suggestions.append(
            "Specify the work location or remote/hybrid arrangement."
        )

    # Salary
    if salary:
        score += 7
        checks.append({
            "name": "Salary",
            "status": "GOOD",
            "message": "Salary information is provided."
        })
    else:
        checks.append({
            "name": "Salary",
            "status": "MISSING",
            "message": "Salary information was not provided."
        })
        suggestions.append(
            "Consider providing a salary range to improve job transparency."
        )

    # Employment type
    if employment_type:
        score += 5
        checks.append({
            "name": "Employment type",
            "status": "GOOD",
            "message": "Employment type is specified."
        })
    else:
        checks.append({
            "name": "Employment type",
            "status": "MISSING",
            "message": "Employment type was not specified."
        })
        suggestions.append(
            "Specify whether the role is full-time, part-time, contract or another type."
        )

    score = min(score, 100)

    if score >= 85:
        quality = "HIGH QUALITY"
    elif score >= 65:
        quality = "GOOD"
    elif score >= 45:
        quality = "NEEDS IMPROVEMENT"
    else:
        quality = "INCOMPLETE"

    return {
        "score": score,
        "quality": quality,
        "checks": checks,
        "suggestions": suggestions,
        "skills_count": len(clean_skills),
        "description_word_count": len(
            re.findall(r"\b[\w+#.-]+\b", description)
        ),
    }
