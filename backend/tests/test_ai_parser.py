from app.services.ai_parser import (
    parse_resume,
    extract_name,
    extract_email,
    extract_phone,
    extract_skills,
    extract_education,
    extract_experience,
)


def test_extract_name():
    text = "Rahul Kumar\nrahul@example.com\nPython Developer"

    assert extract_name(text) == "Rahul Kumar"


def test_extract_email():
    text = "Contact: rahul.kumar@example.com"

    assert extract_email(text) == "rahul.kumar@example.com"


def test_extract_phone():
    text = "Phone: 9876543210"

    assert extract_phone(text) == "9876543210"


def test_extract_skills():
    text = """
    Python developer with experience in SQL,
    FastAPI, React and Docker.
    """

    skills = extract_skills(text)

    assert "Python" in skills
    assert "SQL" in skills
    assert "FastAPI" in skills
    assert "React" in skills
    assert "Docker" in skills


def test_extract_education():
    text = "B.Tech graduate with an MBA."

    education = extract_education(text)

    assert "B.Tech" in education
    assert "MBA" in education


def test_extract_experience():
    text = "Software Developer with 3 years of experience."

    assert extract_experience(text) == ["3"]


def test_extract_experience_with_plus():
    text = "Python Developer with 5+ years of experience."

    assert extract_experience(text) == ["5"]


def test_extract_experience_when_missing():
    text = "Fresh graduate looking for an opportunity."

    assert extract_experience(text) == []


def test_parse_resume():
    text = """
    Rahul Kumar
    rahul@example.com
    9876543210

    B.Tech Computer Science

    Python Developer with 3 years of experience.

    Skills: Python, SQL, FastAPI, Docker
    """

    result = parse_resume(text)

    assert result["name"] == "Rahul Kumar"
    assert result["email"] == "rahul@example.com"
    assert result["phone"] == "9876543210"
    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert "FastAPI" in result["skills"]
    assert "Docker" in result["skills"]
    assert "B.Tech" in result["education"]
    assert result["experience"] == ["3"]


def test_parse_resume_with_empty_text():
    result = parse_resume("")

    assert result["name"] == ""
    assert result["email"] == ""
    assert result["phone"] == ""
    assert result["skills"] == []
    assert result["education"] == []
    assert result["experience"] == []


def test_parse_resume_with_none_text():
    result = parse_resume(None)

    assert result["name"] == ""
    assert result["email"] == ""
    assert result["phone"] == ""
    assert result["skills"] == []
    assert result["education"] == []
    assert result["experience"] == []


def test_skill_parser_does_not_treat_letter_c_as_c_language():
    text = "Experienced developer with communication and cloud experience."

    skills = extract_skills(text)

    assert "C" not in skills


def test_skill_parser_handles_case_insensitive_skills():
    text = "Experienced in python, FASTAPI, docker and javascript."

    skills = extract_skills(text)

    assert "Python" in skills
    assert "FastAPI" in skills
    assert "Docker" in skills
    assert "JavaScript" in skills


def test_experience_parser_handles_year_variations():
    text = "Worked for 2 yrs and previously for 5 YEARS."

    experience = extract_experience(text)

    assert experience == ["2", "5"]
