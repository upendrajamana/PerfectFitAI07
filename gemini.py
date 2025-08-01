import re
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyA8Wpj6dRtk0_trdz8FrKT8IO1e1BTx8yk")

# Initialize the Gemini Pro model globally for reuse
# Changed 'gemini-1.5-pro' to 'gemini-2.0-flash' as requested
gemini_model = genai.GenerativeModel('gemini-2.0-flash')


def _generate_content(prompt: str) -> str:
    """
    Helper function to interact with the Gemini Pro model.
    Handles content generation and basic error catching for all AI calls.
    """
    try:
        response = gemini_model.generate_content(prompt)
        # Access the generated text content from the response object
        return response.text.strip()
    except Exception as e:
        # Print the error for debugging purposes (can be logged in a real application)
        print(f"Gemini API Error: {e}")
        # Return a user-friendly error message
        return f"❗ Error from AI: {str(e)}"


def get_project_idea_response(user_prompt: str) -> str:
    """
    Generates creative, feasible, and useful project ideas based on the user's interest
    using Gemini Pro.
    """
    system_prompt = "You are a helpful AI assistant that gives creative, feasible, and useful project ideas based on the user's interest. Be specific and concise."

    # Combine system and user prompt for Gemini's single turn input
    full_prompt = f"{system_prompt}\n\nUser interest: {user_prompt}"

    return _generate_content(full_prompt)


def get_ai_suggestion_response(user_prompt: str) -> str:
    """
    Provides general AI suggestions or advice based on a user prompt using Gemini Pro.
    """
    system_prompt = "You are a helpful and expert resume advisor. Answer clearly and professionally."

    # Combine system and user prompt
    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    return _generate_content(full_prompt)


def format_review(text: str) -> str:
    """
    Analyzes the formatting of a resume and provides specific feedback
    on bullet points, section alignment, capitalization, punctuation,
    and visual structure using Gemini Pro.
    """
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
    return _generate_content(prompt)


def _extract_numeric_score(text: str) -> int:
    """
    Extracts a numeric score (0-100) from a given text string.
    Looks for patterns like "XX/100" or a standalone number.
    Returns 0 if no valid score is found.
    """
    if not text:
        return 0
    # Try to find "XX/100" pattern first
    match = re.search(r"(\d{1,3})\s*/\s*100", text)
    if match:
        score = int(match.group(1))
        # Ensure the extracted score is within the valid range 0-100
        return min(100, max(0, score))
    # Fallback: try to find any number between 0 and 100
    match = re.search(r"\b(\d{1,2}|100)\b", text)
    if match:
        score = int(match.group(1))
        if 0 <= score <= 100:
            return score
    return 0  # Default score if no valid number is found


def analyze_resume(text: str, presence_score: int, resume_order_score: int, user_description: str = None,
                   order: str = None) -> dict:
    """
    Performs a comprehensive analysis of a resume, including grammar, tailoring score,
    and general content feedback using Gemini Pro.
    """
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

    # --------------------- Grammar and Spelling Check Prompt ------------------------
    grammar_prompt = f"""
Check the grammar of the following resume content. Give:
- A brief summary of key grammar issues.
- Suggestions to improve sentence structure, verb usage, and clarity.
- Then give a grammar score out of 100.

Resume Text:
{text}

❗ Only provide grammar-related feedback.
"""
    grammar_feedback = _generate_content(grammar_prompt)
    grammar_score = _extract_numeric_score(grammar_feedback)

    # --------------------- Resume Match Scoring (Tailoring) ------------------------
    match_score = None
    match_raw = None

    if user_description:
        match_prompt = f"""
You are an AI evaluator. Compare the resume and job description.

Give a **Tailored Match Score out of 100**.

❗ Return ONLY the score in this format: XX/100 (e.g., 85/100)

Resume Text:
{text}

Job Description:
{user_description}
"""
        match_raw = _generate_content(match_prompt)
        match_score = _extract_numeric_score(match_raw)

    # --------------------- Resume Content Analysis ------------------------
    resume_prompt = f"""
You are an expert resume reviewer. Analyze the following resume and provide:

1. A concise key skills summary  
2. Candidate's strengths  
3. Analyze this resume and identify missing or underdeveloped skills that may limit the candidate’s suitability for common job roles in their domain 
4. Resume structure and clarity feedback  
5.Evaluate and score this resume out of 100 based strictly on the depth and quality of the content.
        Focus on:
    Relevance and specificity of skills to real-world roles
    Strength and clarity of experience/project descriptions
    Use of measurable outcomes or impact
    Action-oriented and descriptive language
    Do not reward vague, generic, or filler content (e.g., “did internship”, “worked on project” without details).
    Ignore formatting, grammar, and section order entirely.
    Only return the final content score (out of 100) based on the above criteria.
Resume Text:
{text}

Section Scores:
- Section Presence Score: {presence_score}
- Section Order Score: {resume_order_score}
"""
    if order:
        resume_prompt += f"\nMatched Ideal Section Order:\n{order}"

    analysis = _generate_content(resume_prompt)
    analysis_score = _extract_numeric_score(analysis)

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
