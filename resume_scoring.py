from rapidfuzz import fuzz
import fitz
from docx import Document
import re
import json

# extract text

section_keywords = {
    "Contact Info": ["email", "phone", "contact", "mobile", "personal details"],
    "LinkedIn": ["linkedin", "linkedin.com"],
    "GitHub/Portfolio": ["github", "portfolio", "website", "behance", "dribbble"],
    "Education": ["education", "b.tech", "m.tech", "academic", "university", "degree"],
    "Skills": ["skills", "technologies", "tools", "frameworks", "languages"],
    "Work Experience": ["experience", "work experience", "internship", "employment", "career"],
    "Projects": ["projects", "developed", "built", "created", "implemented", "designed"],
    "Certifications": ["certified", "certification", "course", "training", "license"],
    "Summary": ["objective", "summary", "about me", "profile summary"],
    "Awards": ["awards", "honors", "recognition", "accomplishments"],
    "Activities": ["volunteer", "extracurricular", "activities", "leadership"]
}

section_weights = {
    "Summary": 5,
    "Contact Info": 5,
    "LinkedIn": 3,
    "GitHub/Portfolio": 4,
    "Education": 20,
    "Skills": 15,
    "Work Experience": 10,       # Lowered if fresher; adjust for experienced
    "Internships": 10,
    "Projects": 15,
    "Certifications": 8,
    "Awards": 3,                 # Optional: small bonus
    "Activities": 2              # Optional: small bonus
}

# ideal orders
ideal_orders = [
    # OPTIMAL ORDERS (Score 10) - Most recommended for freshers
    (["Summary", "Education", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Education", "Internships", "Projects", "Skills", "Certifications"], 10),
    (["Education", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Projects", "Education", "Skills", "Certifications"], 10),
    (["Education", "Summary", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Education", "Projects", "Skills", "Experience", "Certifications"], 10),
    (["Education", "Experience", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Education", "Skills", "Projects", "Certifications"], 10),
    (["Education", "Internships", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Projects", "Skills", "Education", "Certifications"], 10),

    # EXCELLENT ORDERS (Score 9) - Highly effective arrangements
    (["Summary", "Education", "Projects", "Certifications", "Skills"], 9),
    (["Education", "Projects", "Summary", "Skills", "Certifications"], 9),
    (["Summary", "Skills", "Education", "Projects", "Certifications"], 9),
    (["Education", "Summary", "Skills", "Projects", "Certifications"], 9),
    (["Summary", "Education", "Internships", "Skills", "Certifications"], 9),
    (["Projects", "Education", "Summary", "Skills", "Certifications"], 9),
    (["Summary", "Education", "Projects", "Awards", "Skills", "Certifications"], 9),
    (["Education", "Skills", "Projects", "Certifications"], 9),
    (["Summary", "Certifications", "Education", "Projects", "Skills"], 9),
    (["Education", "Projects", "Skills", "Summary", "Certifications"], 9),
    (["Summary", "Education", "Projects", "Skills", "GitHub/Portfolio", "Certifications"], 9),
    (["Education", "Summary", "Projects", "Skills", "Activities", "Certifications"], 9),
    (["Summary", "Projects", "Education", "Certifications", "Skills"], 9),
    (["Education", "Internships", "Summary", "Projects", "Skills", "Certifications"], 9),
    (["Summary", "Education", "Skills", "Certifications", "Projects"], 9),

    # VERY GOOD ORDERS (Score 8) - Strong professional arrangements
    (["Summary", "Experience", "Education", "Projects", "Skills", "Certifications"], 8),
    (["Education", "Summary", "Experience", "Projects", "Skills", "Certifications"], 8),
    (["Summary", "Skills", "Projects", "Education", "Experience", "Certifications"], 8),
    (["Projects", "Summary", "Education", "Skills", "Certifications"], 8),
    (["Education", "Projects", "Certifications", "Skills"], 8),
    (["Summary", "Projects", "Skills", "Certifications", "Education"], 8),
    (["Skills", "Education", "Summary", "Projects", "Certifications"], 8),
    (["Summary", "Education", "Projects", "Experience", "Skills", "Certifications"], 8),
    (["Education", "Skills", "Summary", "Projects", "Certifications"], 8),
    (["Summary", "Certifications", "Projects", "Education", "Skills"], 8),
    (["Education", "Summary", "Certifications", "Projects", "Skills"], 8),
    (["Summary", "Education", "Skills", "Projects", "Experience", "Certifications"], 8),
    (["Projects", "Education", "Skills", "Summary", "Certifications"], 8),
    (["Summary", "Projects", "Education", "Skills", "Awards", "Certifications"], 8),
    (["Education", "Internships", "Projects", "Summary", "Skills", "Certifications"], 8),
    (["Summary", "Education", "Projects", "Skills", "Activities", "Certifications"], 8),
    (["Skills", "Summary", "Education", "Projects", "Certifications"], 8),
    (["Education", "Projects", "Summary", "Certifications", "Skills"], 8),
    (["Summary", "Skills", "Education", "Certifications", "Projects"], 8),
    (["Projects", "Skills", "Education", "Summary", "Certifications"], 8),

    # GOOD ORDERS (Score 7) - Acceptable professional formats
    (["Summary", "Experience", "Projects", "Education", "Skills", "Certifications"], 7),
    (["Education", "Experience", "Summary", "Projects", "Skills", "Certifications"], 7),
    (["Projects", "Summary", "Skills", "Education", "Certifications"], 7),
    (["Summary", "Projects", "Skills", "Experience", "Education", "Certifications"], 7),
    (["Education", "Skills", "Projects", "Summary", "Experience", "Certifications"], 7),
    (["Skills", "Projects", "Summary", "Education", "Certifications"], 7),
    (["Summary", "Education", "Projects", "Skills", "LinkedIn", "Certifications"], 7),
    (["Education", "Summary", "Projects", "Skills", "GitHub/Portfolio", "Certifications"], 7),
    (["Summary", "Projects", "Education", "Skills", "Contact Info", "Certifications"], 7),
    (["Projects", "Education", "Summary", "Skills", "Activities", "Certifications"], 7),
    (["Summary", "Skills", "Projects", "Certifications", "Education"], 7),
    (["Education", "Projects", "Skills", "Activities", "Summary", "Certifications"], 7),
    (["Summary", "Education", "Projects", "GitHub/Portfolio", "Skills", "Certifications"], 7),
    (["Skills", "Education", "Projects", "Certifications"], 7),
    (["Summary", "Projects", "Education", "Experience", "Skills", "Certifications"], 7),
    (["Education", "Summary", "Skills", "Certifications", "Projects"], 7),
    (["Projects", "Skills", "Summary", "Education", "Certifications"], 7),
    (["Summary", "Education", "Certifications", "Skills", "Projects"], 7),
    (["Education", "Projects", "Summary", "Skills", "Awards", "Certifications"], 7),
    (["Summary", "Skills", "Certifications", "Education", "Projects"], 7),
    (["Education", "Summary", "Projects", "Certifications", "Skills", "Activities"], 7),
    (["Projects", "Summary", "Education", "Certifications", "Skills"], 7),
    (["Summary", "Education", "Skills", "Projects", "LinkedIn", "Certifications"], 7),
    (["Education", "Projects", "Skills", "Summary", "GitHub/Portfolio", "Certifications"], 7),
    (["Summary", "Projects", "Skills", "Education", "Activities", "Certifications"], 7),

    # ACCEPTABLE ORDERS (Score 6) - Functional but less optimal
    (["Experience", "Summary", "Education", "Projects", "Skills", "Certifications"], 6),
    (["Education", "Experience", "Projects", "Summary", "Skills", "Certifications"], 6),
    (["Skills", "Summary", "Projects", "Education", "Certifications"], 6),
    (["Projects", "Experience", "Summary", "Education", "Skills", "Certifications"], 6),
    (["Summary", "Experience", "Skills", "Projects", "Education", "Certifications"], 6),
    (["Education", "Skills", "Summary", "Experience", "Projects", "Certifications"], 6),
    (["Projects", "Skills", "Education", "Certifications"], 6),
    (["Summary", "Education", "Experience", "Projects", "Certifications", "Skills"], 6),
    (["Education", "Summary", "Experience", "Skills", "Projects", "Certifications"], 6),
    (["Skills", "Projects", "Education", "Summary", "Certifications"], 6),
    (["Summary", "Projects", "Experience", "Skills", "Education", "Certifications"], 6),
    (["Education", "Projects", "Experience", "Summary", "Skills", "Certifications"], 6),
    (["Projects", "Summary", "Skills", "Experience", "Education", "Certifications"], 6),
    (["Summary", "Skills", "Experience", "Projects", "Education", "Certifications"], 6),
    (["Education", "Skills", "Projects", "Experience", "Summary", "Certifications"], 6),
    (["Skills", "Education", "Summary", "Experience", "Projects", "Certifications"], 6),
    (["Summary", "Education", "Projects", "Experience", "Certifications", "Skills"], 6),
    (["Projects", "Education", "Skills", "Experience", "Summary", "Certifications"], 6),
    (["Education", "Summary", "Projects", "Experience", "Skills", "LinkedIn", "Certifications"], 6),
    (["Summary", "Projects", "Skills", "Experience", "Certifications", "Education"], 6),

    # SHORT RESUME FORMATS (2-3 sections) with scores below 4
    (["Education", "Skills"], 3),
    (["Projects", "Skills"], 3),
    (["Summary", "Education"], 2),
    (["Education", "Projects"], 3),
    (["Skills", "Projects"], 3),
    (["Summary", "Skills"], 2),
    (["Education", "Certifications"], 3),
    (["Projects", "Certifications"], 3),
    (["Summary", "Projects"], 3),
    (["Skills", "Certifications"], 2),
    (["Education", "Skills", "Projects"], 3),
    (["Summary", "Education", "Skills"], 3),
    (["Projects", "Skills", "Certifications"], 3),
    (["Education", "Projects", "Certifications"], 3),
    (["Summary", "Projects", "Skills"], 3),

    # ADDITIONAL COMPREHENSIVE ORDERS (Score 6-8)
    (["Summary", "Education", "Projects", "Skills", "Awards", "GitHub/Portfolio", "Certifications"], 7),
    (["Education", "Summary", "Internships", "Projects", "Skills", "Activities", "Certifications"], 8),
    (["Summary", "Projects", "Education", "Skills", "LinkedIn", "Contact Info", "Certifications"], 6),
    (["Education", "Projects", "Summary", "Skills", "GitHub/Portfolio", "Awards", "Certifications"], 7),
    (["Summary", "Skills", "Education", "Projects", "Activities", "LinkedIn", "Certifications"], 6),
    (["Projects", "Education", "Summary", "Skills", "Certifications", "Contact Info"], 7),
    (["Education", "Summary", "Projects", "Skills", "Certifications", "LinkedIn"], 8),
    (["Summary", "Education", "Skills", "Projects", "GitHub/Portfolio", "Awards", "Certifications"], 7),
    (["Projects", "Skills", "Education", "Summary", "Activities", "Certifications"], 7),
    (["Education", "Projects", "Skills", "Summary", "LinkedIn", "Certifications"], 7),
    (["Summary", "Projects", "Skills", "Education", "Contact Info", "Activities", "Certifications"], 6),
    (["Education", "Summary", "Skills", "Projects", "GitHub/Portfolio", "LinkedIn", "Certifications"], 6),
    (["Projects", "Education", "Skills", "Summary", "Awards", "Activities", "Certifications"], 6),
    (["Summary", "Education", "Projects", "Certifications", "Skills", "LinkedIn"], 8),
    (["Education", "Projects", "Summary", "Certifications", "Skills", "GitHub/Portfolio"], 7),

    # SPECIALIZED ARRANGEMENTS (Score 6-9)
    (["GitHub/Portfolio", "Projects", "Education", "Skills", "Summary", "Certifications"], 8),
    (["Summary", "GitHub/Portfolio", "Projects", "Education", "Skills", "Certifications"], 8),
    (["Education", "GitHub/Portfolio", "Projects", "Summary", "Skills", "Certifications"], 8),
    (["Projects", "GitHub/Portfolio", "Education", "Skills", "Summary", "Certifications"], 9),
    (["Summary", "LinkedIn", "Education", "Projects", "Skills", "Certifications"], 7),
    (["Education", "LinkedIn", "Projects", "Summary", "Skills", "Certifications"], 7),
    (["Projects", "LinkedIn", "Education", "Skills", "Summary", "Certifications"], 7),
    (["Summary", "Awards", "Education", "Projects", "Skills", "Certifications"], 8),
    (["Education", "Awards", "Projects", "Summary", "Skills", "Certifications"], 8),
    (["Projects", "Awards", "Education", "Skills", "Summary", "Certifications"], 8),
    (["Summary", "Activities", "Education", "Projects", "Skills", "Certifications"], 7),
    (["Education", "Activities", "Projects", "Summary", "Skills", "Certifications"], 7),
    (["Projects", "Activities", "Education", "Skills", "Summary", "Certifications"], 7),
    (["Summary", "Contact Info", "Education", "Projects", "Skills", "Certifications"], 6),
    (["Education", "Contact Info", "Projects", "Summary", "Skills", "Certifications"], 6),

    # EXPERIENCE-FOCUSED VARIATIONS (Score 6-8)
    (["Experience", "Education", "Projects", "Summary", "Skills", "Certifications"], 7),
    (["Summary", "Experience", "Education", "Skills", "Projects", "Certifications"], 8),
    (["Education", "Experience", "Summary", "Skills", "Projects", "Certifications"], 7),
    (["Projects", "Experience", "Education", "Summary", "Skills", "Certifications"], 7),
    (["Skills", "Experience", "Education", "Projects", "Summary", "Certifications"], 6),
    (["Summary", "Education", "Experience", "Skills", "Projects", "Certifications"], 8),
    (["Education", "Summary", "Experience", "Projects", "Certifications", "Skills"], 7),
    (["Projects", "Summary", "Experience", "Education", "Skills", "Certifications"], 7),
    (["Skills", "Summary", "Experience", "Education", "Projects", "Certifications"], 6),
    (["Summary", "Projects", "Experience", "Education", "Certifications", "Skills"], 7),

    # INTERNSHIP-FOCUSED VARIATIONS (Score 7-9)
    (["Internships", "Education", "Projects", "Summary", "Skills", "Certifications"], 8),
    (["Summary", "Internships", "Education", "Skills", "Projects", "Certifications"], 9),
    (["Education", "Internships", "Summary", "Projects", "Skills", "Certifications"], 9),
    (["Projects", "Internships", "Education", "Summary", "Skills", "Certifications"], 8),
    (["Skills", "Internships", "Education", "Projects", "Summary", "Certifications"], 7),
    (["Summary", "Education", "Internships", "Projects", "Certifications", "Skills"], 8),
    (["Education", "Summary", "Internships", "Skills", "Projects", "Certifications"], 8),
    (["Projects", "Summary", "Internships", "Education", "Skills", "Certifications"], 8),
    (["Skills", "Summary", "Internships", "Education", "Projects", "Certifications"], 7),
    (["Summary", "Projects", "Internships", "Education", "Skills", "Certifications"], 8),

    # SKILLS-FIRST VARIATIONS (Score 6-8)
    (["Skills", "Summary", "Education", "Projects", "Certifications"], 7),
    (["Skills", "Education", "Summary", "Projects", "Certifications"], 7),
    (["Skills", "Projects", "Summary", "Education", "Certifications"], 8),
    (["Skills", "Summary", "Projects", "Education", "Experience", "Certifications"], 7),
    (["Skills", "Education", "Projects", "Summary", "Experience", "Certifications"], 7),
    (["Skills", "Projects", "Education", "Summary", "Experience", "Certifications"], 7),
    (["Skills", "Summary", "Education", "Experience", "Projects", "Certifications"], 6),
    (["Skills", "Education", "Summary", "Experience", "Projects", "Certifications"], 6),
    (["Skills", "Projects", "Summary", "Experience", "Education", "Certifications"], 6),
    (["Skills", "Summary", "Projects", "Experience", "Education", "Certifications"], 6),

    # CERTIFICATIONS-PROMINENT VARIATIONS (Score 7-9)
    (["Certifications", "Summary", "Education", "Projects", "Skills"], 8),
    (["Certifications", "Education", "Summary", "Projects", "Skills"], 8),
    (["Certifications", "Projects", "Summary", "Education", "Skills"], 8),
    (["Summary", "Certifications", "Education", "Skills", "Projects"], 9),
    (["Education", "Certifications", "Summary", "Projects", "Skills"], 8),
    (["Projects", "Certifications", "Summary", "Education", "Skills"], 8),
    (["Skills", "Certifications", "Summary", "Education", "Projects"], 7),
    (["Summary", "Education", "Certifications", "Projects", "Skills"], 9),
    (["Education", "Summary", "Certifications", "Skills", "Projects"], 8),
    (["Projects", "Summary", "Certifications", "Education", "Skills"], 8),

    # MIXED COMPREHENSIVE ORDERS (Score 6-8)
    (["Summary", "Education", "Projects", "Skills", "Experience", "GitHub/Portfolio", "Certifications"], 7),
    (["Education", "Summary", "Projects", "Skills", "Internships", "Activities", "Certifications"], 8),
    (["Projects", "Summary", "Education", "Skills", "Awards", "LinkedIn", "Certifications"], 7),
    (["Skills", "Summary", "Education", "Projects", "GitHub/Portfolio", "Contact Info", "Certifications"], 6),
    (["Summary", "Projects", "Education", "Skills", "LinkedIn", "Awards", "Certifications"], 7),
    (["Education", "Projects", "Summary", "Skills", "Activities", "GitHub/Portfolio", "Certifications"], 7),
    (["Projects", "Education", "Summary", "Skills", "Contact Info", "LinkedIn", "Certifications"], 6),
    (["Summary", "Skills", "Education", "Projects", "GitHub/Portfolio", "Activities", "Certifications"], 6),
    (["Education", "Skills", "Summary", "Projects", "LinkedIn", "Awards", "Certifications"], 7),
    (["Projects", "Skills", "Summary", "Education", "GitHub/Portfolio", "Contact Info", "Certifications"], 6),

    # FINAL VARIATIONS TO REACH 200 (Score 6-8)
    (["Summary", "Education", "Skills", "Experience", "Projects", "LinkedIn", "Certifications"], 7),
    (["Education", "Summary", "Skills", "Internships", "Projects", "GitHub/Portfolio", "Certifications"], 8),
    (["Projects", "Summary", "Skills", "Education", "Awards", "Contact Info", "Certifications"], 7),
    (["Skills", "Summary", "Education", "Experience", "Projects", "Activities", "Certifications"], 6),
    (["Summary", "Projects", "Skills", "Internships", "Education", "LinkedIn", "Certifications"], 7),
    (["Education", "Projects", "Skills", "Summary", "GitHub/Portfolio", "Contact Info", "Certifications"], 6),
    (["Projects", "Education", "Skills", "Summary", "Awards", "Activities", "LinkedIn", "Certifications"], 6),
    (["Summary", "Skills", "Projects", "Education", "Experience", "GitHub/Portfolio", "LinkedIn", "Certifications"], 6),
    (["Education", "Skills", "Projects", "Summary", "Internships", "Awards", "Contact Info", "Certifications"], 6),
    (["Projects", "Skills", "Education", "Summary", "Activities", "LinkedIn", "GitHub/Portfolio", "Certifications"], 6)
]

def detect_sections(text):
    found_sections = []
    lower_text = text.lower()

    for section, keywords in section_keywords.items():
        for keyword in keywords:
            if keyword.lower() in lower_text and section not in found_sections:
                found_sections.append(section)
                break  # avoid duplicate entries for same section

    return found_sections


def extract_text(file_path, file_ext):
    text = ""

    if file_ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()

    elif file_ext == ".docx":
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])

    elif file_ext == ".txt":
        with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
            text = f.read()

    else:
        text = "❌ Unsupported file format."

    return text


# scoring resume match the keywords with fuzz

def has_fuzzy_match(text, keywords, threshold=75):
    for keyword in keywords:
        if fuzz.partial_ratio(keyword.lower(), text.lower()) >= threshold:
            return True
    return False


def score_resume(text, detected_sections):
    presence_score = 0

    # --- 1. Section presence score ---
    for section, keywords in section_keywords.items():
        if has_fuzzy_match(text, keywords):
            presence_score += section_weights.get(section, 0)
    resume_order_score = 0

    # --- 2. Ideal order scoring ---
    def longest_common_subsequence(X, Y):
        m, n = len(X), len(Y)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if X[i] == Y[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
        return dp[m][n]

    order_score = 0
    best_matching_order = []
    best_lcs_len = 0

    for ideal_order, ideal_score in ideal_orders:
        lcs_len = longest_common_subsequence(ideal_order, detected_sections)

        if lcs_len > best_lcs_len:
            best_lcs_len = lcs_len
            best_matching_order = ideal_order

        if lcs_len == len(ideal_order):
            order_score = max(order_score, ideal_score)
        elif lcs_len >= len(ideal_order) - 1:
            order_score = max(order_score, ideal_score - 1)
        elif lcs_len >= len(ideal_order) - 2:
            order_score = max(order_score, ideal_score - 2)

    return presence_score, order_score, best_matching_order


# --- NEW SCORING COMPONENTS ---

def calculate_resume_length_score(text, is_fresher=True):
    """
    Calculate resume length score based on word count.

    Args:
        text (str): Resume text
        is_fresher (bool): True for fresher, False for experienced

    Returns:
        int: Resume length score (0-100)
    """
    # Count words (split by whitespace and filter empty strings)
    words = [word for word in text.split() if word.strip()]
    word_count = len(words)

    if is_fresher:
        # Ideal range for freshers: 400-600 words
        min_words, max_words = 400, 600
    else:
        # Ideal range for experienced: 700-1000 words
        min_words, max_words = 700, 1000

    # Perfect score if within ideal range
    if min_words <= word_count <= max_words:
        return 100

    # Calculate penalty for deviation
    if word_count < min_words:
        deviation = min_words - word_count
    else:  # word_count > max_words
        deviation = word_count - max_words

    # Penalty: 0.5 points per word deviation
    penalty = deviation * 0.5
    score = max(0, 100 - penalty)  # Ensure score doesn't go below 0

    return int(score)


def extract_summary_section(text):
    """
    Extract summary/objective section from resume text.

    Args:
        text (str): Full resume text

    Returns:
        str: Summary section text or empty string if not found
    """
    summary_patterns = [
        r'(?i)(objective|summary|about me|profile summary)\s*:?\s*\n(.*?)(?=\n\s*[A-Z][A-Za-z\s]*:|$)',
        r'(?i)(objective|summary|about me|profile summary)\s*:?\s*(.*?)(?=\n\s*[A-Z][A-Za-z\s]*:|$)',
    ]

    for pattern in summary_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(2).strip()

    return ""


def calculate_tailoring_score(text, job_description, detected_sections):
    """
    Calculate how well the resume is tailored to the job description.

    Args:
        text (str): Resume text
        job_description (str): Job description text
        detected_sections (list): List of detected sections

    Returns:
        int: Tailoring score (0-100)
    """
    if not job_description:
        return 0

    # Extract keywords from job description (simple tokenization)
    jd_words = set()
    for word in job_description.lower().split():
        # Clean word (remove punctuation) and filter out common words
        clean_word = re.sub(r'[^\w]', '', word)
        if len(clean_word) > 2 and clean_word not in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                                                      'with', 'by']:
            jd_words.add(clean_word)

    if not jd_words:
        return 0

    # Determine text to match against
    if "Summary" in detected_sections:
        # If summary present, match keywords only with summary
        summary_text = extract_summary_section(text)
        match_text = summary_text if summary_text else text
    else:
        # Fall back to full resume text
        match_text = text

    # Count matching keywords (case-insensitive)
    resume_words = set()
    for word in match_text.lower().split():
        clean_word = re.sub(r'[^\w]', '', word)
        if len(clean_word) > 2:
            resume_words.add(clean_word)

    # Calculate overlap
    matching_keywords = jd_words.intersection(resume_words)

    if len(jd_words) == 0:
        return 0

    # Calculate score as percentage of job description keywords found
    tailoring_score = (len(matching_keywords) / len(jd_words)) * 100

    return min(100, int(tailoring_score))


def comprehensive_resume_score(text, job_description="", is_fresher=True):
    """
    Calculate comprehensive resume score with all components.

    Args:
        text (str): Resume text
        job_description (str): Job description text
        is_fresher (bool): True for fresher, False for experienced

    Returns:
        dict: Complete scoring breakdown
    """
    # Existing scoring logic
    detected_sections = detect_sections(text)
    presence_score, order_score, best_matching_order = score_resume(text, detected_sections)

    # New scoring components
    length_score = calculate_resume_length_score(text, is_fresher)
    tailoring_score = calculate_tailoring_score(text, job_description, detected_sections)

    # Calculate weighted total score
    # Weights: presence (30%), order (20%), tailoring (30%), length (20%)
    total_score = (
            presence_score * 0.3 +
            order_score * 0.2 +
            tailoring_score * 0.3 +
            length_score * 0.2
    )

    return {
        "section_presence_score": presence_score,
        "section_order_score": order_score,
        "tailoring_score": tailoring_score,
        "resume_length_score": length_score,
        "total_score": round(total_score, 2),
        "detected_sections": detected_sections,
        "best_matching_order": best_matching_order,
        "word_count": len([word for word in text.split() if word.strip()]),
        "is_fresher": is_fresher
    }