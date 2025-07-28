from rapidfuzz import fuzz
import fitz
from docx import Document
#extract text

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
    "LinkedIn": 5,
    "GitHub/Portfolio": 5,
    "Education": 15,
    "Skills": 15,
    "Work Experience": 20,
    "Internships": 10,
    "Projects": 10,
    "Certifications": 5,
    "Awards": 0,         # Optional: bonus
    "Activities": 0      # Optional: bonus
}
#ideal orders
ideal_orders = [
    (["Summary", "Experience", "Education", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Education", "Internships", "Projects", "Skills", "Certifications"], 10),
    (["Education", "Experience", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Education", "Projects", "Skills", "Certifications"], 10),
    (["Education", "Projects", "Skills", "Certifications"], 10),
    (["Summary", "Experience", "Projects", "Skills", "Certifications"], 9),
    (["Summary", "Experience", "Projects", "Skills", "Certifications"], 9),
    (["Summary", "Skills", "Education", "Projects", "Experience", "Certifications"], 8),
    (["Summary", "Experience", "Education", "Projects", "Certifications"], 8),
    (["Summary", "Experience", "Hobbies", "Education", "Projects", "Skills", "Certifications"], 7),
    (["Summary", "Education", "Projects", "Skills", "Contact Info", "Certifications"], 9),
    (["Summary", "Education", "Projects", "Awards", "Skills", "Certifications"], 9),
    (["Summary", "Projects", "Experience", "Education", "Skills", "Certifications"], 8),
    (["Summary", "Education", "Skills", "Experience", "Projects", "Certifications"], 8),
    (["Summary", "Education", "Projects", "GitHub/Portfolio", "Skills", "Certifications"], 7),
    (["Summary", "Education", "Projects", "Skills", "Certifications", "Awards"], 7),
    (["Education", "Summary", "Experience", "Skills", "Certifications", "Projects"], 6),
    (["Education", "Skills", "Summary", "Certifications", "Projects"], 6),
    (["Education", "Summary", "Certifications", "Skills", "Projects", "GitHub/Portfolio"], 6),
    (["Experience", "Summary", "Education", "Skills", "Projects", "Certifications"], 6),
    (["Summary", "Education", "Projects", "Experience", "Skills", "Certifications"], 10),
    (["Summary", "Projects", "Education", "Skills", "Certifications"], 9),
    (["Summary", "Education", "Projects", "Certifications", "Skills"], 9),
    (["Summary", "Education", "Skills", "Certifications", "Projects"], 9),
    (["Summary", "Education", "Certifications", "Projects", "Skills"], 9),
    (["Summary", "Certifications", "Education", "Projects", "Skills"], 8),
    (["Education", "Summary", "Projects", "Certifications", "Skills"], 8),
    (["Projects", "Education", "Summary", "Skills", "Certifications"], 7),
    (["Skills", "Education", "Projects", "Summary", "Certifications"], 7),
    (["Education", "Skills", "Projects", "Summary", "Certifications"], 7),
    (["Summary", "Projects", "Skills", "Education", "Certifications"], 9),
    (["Summary", "Education", "Certifications", "GitHub/Portfolio", "Projects", "Skills"], 9),
    (["Summary", "Projects", "Education", "Skills", "Certifications", "Awards"], 8),
    (["Education", "Summary", "Projects", "Skills", "Activities", "Certifications"], 8),
    (["Summary", "Education", "Skills", "Projects", "Certifications", "Activities"], 8),
    (["Education", "Summary", "Projects", "Skills", "Certifications", "Hobbies"], 7),
    (["Summary", "Education", "Projects", "Certifications", "LinkedIn", "Skills"], 7),
    (["Summary", "Projects", "Education", "Certifications", "Skills", "Contact Info"], 7),
    (["Summary", "Education", "Projects", "Skills", "GitHub/Portfolio", "Certifications"], 6),
    (["Education", "Experience", "Projects", "Activities", "Skills", "Certifications"], 6),
    (["Summary", "Education", "Internships", "Skills", "Certifications"], 9),
    (["Summary", "Education", "Projects", "Skills", "Awards", "Certifications"], 8),
    (["Summary", "Education", "Projects", "Experience", "Certifications", "Skills"], 8),
    (["Education", "Summary", "Skills", "Projects", "Certifications"], 7),
    (["Summary", "Skills", "Projects", "Education", "Certifications"], 7),
    (["Summary", "Projects", "Education", "Skills", "Certifications", "LinkedIn"], 7),
    (["Education", "Summary", "Projects", "Certifications", "GitHub/Portfolio", "Skills"], 6),
    (["Summary", "Certifications", "Education", "Projects", "Skills", "LinkedIn"], 6),
    (["Projects", "Education", "Summary", "Certifications", "Skills", "LinkedIn"], 6),
    (["Education", "Summary", "Projects", "Skills", "Certifications", "GitHub/Portfolio"], 6)
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

    order_score = 6
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
