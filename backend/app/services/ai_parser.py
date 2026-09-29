import re


SKILLS = [
    "Python",
    "Java",
    "C",
    "C++",
    "SQL",
    "MySQL",
    "FastAPI",
    "Flask",
    "Django",
    "Machine Learning",
    "Deep Learning",
    "TensorFlow",
    "PyTorch",
    "HTML",
    "CSS",
    "JavaScript",
    "React",
    "Node.js",
    "Git",
    "Docker",
]


EDUCATION = [
    "B.Tech",
    "M.Tech",
    "BCA",
    "MCA",
    "B.Sc",
    "M.Sc",
    "B.E",
    "M.E",
    "MBA",
    "Diploma",
    "PhD",
]


def parse_resume(text):
    """
    Parse resume text into structured candidate information.
    """

    text = text or ""

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
    }


def extract_name(text):
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()

        if len(line) > 2 and len(line.split()) <= 4:
            return line

    return ""


def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text,
    )

    return match.group() if match else ""


def extract_phone(text):
    match = re.search(
        r"\b\d{10}\b",
        text,
    )

    return match.group() if match else ""


def extract_skills(text):
    found = []

    for skill in SKILLS:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            found.append(skill)

    return found


def extract_education(text):
    found = []

    for degree in EDUCATION:
        pattern = rf"(?<!\w){re.escape(degree)}(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            found.append(degree)

    return found


def extract_experience(text):
    pattern = r"(\d+)\+?\s*(?:years?|yrs?)"

    matches = re.findall(pattern, text, re.IGNORECASE)

    return matches
