from openai import OpenAI
import re
import openai
client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)

def get_project_idea_response(user_prompt):
    system_prompt = "You are a helpful AI assistant that gives creative, feasible, and useful project ideas based on the user's interest. Be specific and concise."

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❗ Error generating project idea: {str(e)}"



def get_ai_suggestion_response(user_prompt):
    system_prompt = "You are a helpful and expert resume advisor. Answer clearly and professionally."

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❗ Error generating suggestion: {str(e)}"



def format_review(text):
    prompt = f"""
You are an expert resume reviewer focusing only on formatting.

Please analyze the formatting of the following resume and provide suggestions on:

1. Bullet point usage – are they consistent and properly used?
2. Section alignment – is there a proper order (e.g., Summary → Education → Experience → Skills)?
3. Capitalization and punctuation consistency
4. Visual structure and readability in plain text format

Resume Text:
{text}

Give only formatting-related feedback in bullet points.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful AI resume format evaluator."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Error in formatting analysis: {str(e)}"

def extract_numeric_score(text):
    if not text:
        return None
    match = re.search(r"(\d{2,3})\s*/\s*100", text)
    if match:
        return int(match.group(1))
    # fallback: extract 50-100 number
    match = re.search(r"\b([5-9][0-9]|100)\b", text)
    if match:
        return int(match.group(1))
    return None


def analyze_resume(text, presence_score, resume_order_score, user_description=None, order=None):
    if not text:
        return {
            "analysis": "Error: Resume text is empty.",
            "match_score": None,
            "match_score_text": None,
            "analysis_score": 0,
            "grammar_score": 0,
            "grammar_feedback": "No resume provided.",
            "total_score": 0
        }

    # --------------------- Grammar Check Prompt ------------------------
    grammar_prompt = f"""
Check the grammar of the following resume content. Give:
- A brief summary of key grammar issues.
- Suggestions to improve sentence structure, verb usage, and clarity.
- Then give a grammar score out of 100.

Resume Text:
{text}

❗ Only provide grammar-related feedback.
"""

    grammar_feedback = ""
    grammar_score = 0

    try:
        grammar_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful grammar reviewer for resumes."},
                {"role": "user", "content": grammar_prompt}
            ]
        )
        grammar_feedback = grammar_response.choices[0].message.content.strip()
        grammar_score = extract_numeric_score(grammar_feedback) or 0
    except Exception as e:
        grammar_feedback = f"Error in grammar analysis: {str(e)}"
        grammar_score = 0

    # --------------------- Resume Match Scoring ------------------------
    match_score = None
    match_raw = None

    if user_description:
        match_prompt = f"""
You are an AI evaluator. Compare the resume and job description.

Give a **Tailored Match Score out of 100**.

❗ Return ONLY the score in this format: 85/100

Resume Text:
{text}

Job Description:
{user_description}
"""
        try:
            match_response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You evaluate resume-job fit."},
                    {"role": "user", "content": match_prompt}
                ]
            )
            match_raw = match_response.choices[0].message.content.strip()
            match_score = extract_numeric_score(match_raw)
        except Exception as e:
            match_raw = f"Error: {str(e)}"
            match_score = None

    # --------------------- Resume Content Analysis ------------------------
    resume_prompt = f"""
You are an expert resume reviewer. Analyze the following resume and provide:

1. A concise key skills summary  
2. Candidate's strengths  
3. Missing skills or gaps for a Data Scientist role  
4. Resume structure and clarity feedback  
5. Score the resume out of 100

Resume Text:
{text}

Section Scores:
- Section Presence Score: {presence_score}
- Section Order Score: {resume_order_score}
"""
    if order:
        resume_prompt += f"\nMatched Ideal Section Order:\n{order}"

    analysis_score = 0
    analysis = ""

    try:
        analysis_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful AI resume analyzer."},
                {"role": "user", "content": resume_prompt}
            ]
        )
        analysis = analysis_response.choices[0].message.content.strip()
        analysis_score = extract_numeric_score(analysis) or 0
    except Exception as e:
        analysis = f"Error in analysis: {str(e)}"
        analysis_score = 0

    # --------------------- Total Score ------------------------
    total_score = presence_score + resume_order_score + analysis_score + grammar_score
    if match_score is not None:
        total_score += match_score

    return {
        "analysis": analysis,
        "match_score": match_score,
        "match_score_text": match_raw,
        "analysis_score": analysis_score,
        "grammar_score": grammar_score,
        "grammar_feedback": grammar_feedback,
        "total_score": total_score
    }

