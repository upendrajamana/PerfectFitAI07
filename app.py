import json

from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
import os
from resume_scoring import extract_text, score_resume, detect_sections,calculate_resume_length_score
from gemini import analyze_resume, format_review,get_ai_suggestion_response
from gemini import analyze_resume, format_review,get_ai_suggestion_response,get_project_idea_response
from datetime import datetime
import re
from flask import session
from gemini import get_ai_suggestion_response  # ✅ import new function
import firebase_admin
from firebase_admin import credentials, firestore
import random
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
from all_scores import ResumeAnalyzer

cred = credentials.Certificate("fire.json")  # Your JSON filename
firebase_admin.initialize_app(cred)
db = firestore.client()




load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("grop_api_key")

# Use absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAVE_FOLDER = os.path.join(BASE_DIR, 'descriptions')

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Global state
last_resume_text = ""
last_detected_sections = []
last_user_description = ""
analysis = ""
match_score = 0
analysis_score = 0
total_score = 0
presence_score = 0
resume_order_score = 0

analyzer = ResumeAnalyzer()


@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"answer": "Please enter a question."})

    answer = get_ai_suggestion_response(question)
    return jsonify({"answer": answer})

@app.route("/ask_project_idea", methods=["POST"])
def ask_project_idea():
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"answer": "Please enter your area of interest or goal."})

    answer = get_project_idea_response(question)
    return jsonify({"answer": answer})


def extract_analysis_score(analysis_text):
    if not analysis_text:
        return None

    # Match patterns like "82/100", "82 out of 100", "score: 82", "rated 82", "82."
    match = re.search(r"\b(100|\d{1,2})\b\s*(?:/|out of)?\s*100?", analysis_text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        if 0 <= score <= 100:
            return score

    return None


def calculate_total_score(presence_score, order_score, analysis_score, match_score=None):
    if match_score is not None:
        return round((presence_score / 100) * 25 + (order_score / 100) * 20 + (analysis_score / 100) * 25 + (match_score / 100) * 30, 2)
    else:
        return round((presence_score / 100) * 35 + (order_score / 100) * 30 + (analysis_score / 100) * 35, 2)

grammar_score=0
@app.route('/')
def home():
    return render_template(
        'index.html',
        uploaded=bool(last_resume_text),
        total_score=total_score,
        analysis_score=analysis_score,             # CONTENT SCORE
        resume_order_score=resume_order_score,     # SECTION ORDER
        grammar_score=grammar_score,               # GRAMMAR
        presence_score=presence_score  # SECTION PRESENCE

    )


@app.route('/know')
def know_more():
    return render_template('know.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        subject = request.form['subject']
        message = request.form['message']

        about_dir = os.path.join(BASE_DIR, "about")
        os.makedirs(about_dir, exist_ok=True)
        with open(os.path.join(about_dir, "contact_submissions.txt"), "a") as f:
            f.write(f"Name: {name}\nEmail: {email}\nPhone: {phone}\nSubject: {subject}\nMessage: {message}\n---\n")

        flash("Thanks! We'll get back to you soon.")
        return redirect(url_for('contact'))

    return render_template("contact.html")


@app.route('/dashboard')
def dashboard():
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('signin'))

    user_doc = db.collection('users').document(user_email).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return render_template('index.html', user=user_data)
    else:
        flash('User session not valid')
        return redirect(url_for('signin'))



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/upload', methods=['POST'])
def upload_resume():
    global last_resume_text, last_detected_sections, analysis
    global match_score, analysis_score, total_score
    global presence_score, resume_order_score,grammar_score,job_description,length_score,results

    if 'resume' not in request.files:
        flash('No resume file part')
        return redirect(url_for('home'))

    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('home'))

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)
    last_resume_text = extract_text(filepath, ext)
    flash('Resume successfully uploaded.')

    # Analyze now
    last_detected_sections = detect_sections(last_resume_text)
    presence_score, resume_order_score, order = score_resume(last_resume_text, last_detected_sections)
    length_score=calculate_resume_length_score(last_resume_text, True)

    result = analyze_resume(last_resume_text, presence_score, resume_order_score, last_user_description, order)

    analysis = result.get("analysis", "")
    match_score = result.get("match_score") or 0
    analysis_score = extract_analysis_score(analysis) or 0
    grammar_score = result.get("grammar_score") or 0  # ✅ This is how you fetch grammar score

    # Final total score
    # Weights when JD is given
    #all scores#########################################




    # Weights when JD is NOT given
    weights_no_jd = {
        "presence": 0.15,
        "order": 0.15,
        "analysis": 0.60,  # reduced from 0.70
        "grammar": 0.06,
        "length": 0.09
    }
    if analysis_score < 10:
        grammar_score=0   # or use another function if needed


    total_score = (
            presence_score * weights_no_jd["presence"] +
            resume_order_score * weights_no_jd["order"] +
            analysis_score * weights_no_jd["analysis"] +
            grammar_score * weights_no_jd["grammar"]+
            length_score * weights_no_jd["length"]
    )

    total_score = round(min(total_score, 100), 2)
    # Cap at 100 and round
    # Cap at 100

    # Store scores in session
    session['grammar_score'] = grammar_score
    session['total_score'] = total_score

    return redirect(url_for('home'))


@app.route('/score')
def show_score():
    results = analyzer.analyze_resume(last_resume_text)
    return render_template('new.html',
                           # Existing scores
                           match_score=match_score,
                           analysis_score=analysis_score,
                           resume_order=resume_order_score,
                           presence_score=presence_score,
                           total_score=total_score,
                           analysis=analysis,

                           # Add feedback for existing sections (you'll need to provide these)
                           match_feedback="Job tailoring analysis feedback here",
                           analysis_feedback="Content quality analysis feedback here",
                           order_feedback="Resume format analysis feedback here",
                           presence_feedback="Section presence analysis feedback here",

                           # New scores from results
                           quantify_score=results['quantify_impact']['score'],
                           quantify_feedback=results['quantify_impact']['feedback'],

                           unnecessary_score=results['unnecessary_sections']['score'],
                           unnecessary_feedback=results['unnecessary_sections']['feedback'],

                           contact_score=results['contact_details']['score'],
                           contact_feedback=results['contact_details']['feedback'],

                           dates_score=results['date_consistency']['score'],
                           dates_feedback=results['date_consistency']['feedback'],

                           keywords_score=results['keywords']['score'],
                           keywords_feedback=results['keywords']['feedback'],

                           verbs_score=results['action_verbs']['score'],
                           verbs_feedback=results['action_verbs']['feedback'],

                           achievements_score=results['achievements']['score'],
                           achievements_feedback=results['achievements']['feedback'],

                           grammar_score=results['grammar']['score'],
                           grammar_feedback=results['grammar']['feedback']
                           )

@app.route('/feature/1')
def ats_checker():
    if not last_resume_text:
        return redirect(url_for('home'))


    return render_template(
        "ats.html",
        score=presence_score,
        analysis=analysis,
        resume_order=resume_order_score,
        match_score=match_score,
        analysis_score=analysis_score,
        total_score=total_score,


    )


@app.route('/signin/3', methods=['GET', 'POST'])
def signin3():
    return render_template('signin.html')  # or another file if different


@app.route('/signin/2', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        users_ref = db.collection('users')
        user_doc = users_ref.document(email).get()

        if user_doc.exists:
            stored_data = user_doc.to_dict()
            if check_password_hash(stored_data['password'], password):
                session['user'] = email
                return redirect(url_for('home'))  # redirect to home page
            else:
                flash('Incorrect password')
        else:
            flash('User not found. Please sign up.')

    return render_template("signin.html")

from flask import Flask, render_template, request, redirect
from firebase_admin import firestore
from werkzeug.security import generate_password_hash

db = firestore.client()  # assumes firebase_admin.initialize_app() is already done


@app.route('/signup/3', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')

        user_ref = db.collection("users").document(email)
        user_doc = user_ref.get()

        if user_doc.exists:
            return render_template("signup.html", message="⚠️ Account already exists. Please sign in.")

        # ✅ Hash the password before storing
        hashed_password = generate_password_hash(password)

        # ✅ Store user in Firestore
        user_ref.set({
            "name": name,
            "email": email,
            "password": hashed_password  # Secure storage
        })

        return redirect("/signin/2")

    return render_template("signup.html")


@app.route('/feature/2')
def format_feedback():
    if not last_resume_text:
        return redirect(url_for('home'))

    format_analysis = format_review(last_resume_text)
    return render_template("format_feedback.html", analysis=format_analysis)

@app.route("/feature/4")
def feature_4():
    return render_template("suggestions.html")

@app.route("/feature/5")
def feature_5():
    return render_template("projects.html")
@app.route('/popular-resumes', methods=['GET', 'POST'])
def popular_resumes():
    resumes = []
    folder_path = os.path.join('static', 'resumes')

    if os.path.exists(folder_path):
        all_files = [f for f in os.listdir(folder_path) if f.endswith('.png') or f.endswith('.jpg')]

        if all_files:  # ✅ make sure it's not empty
            resumes = [
                {'file': f, 'url': url_for('static', filename=f'resumes/{f}')}
                for f in all_files
            ]

    return render_template('popular_resumes.html', resumes=resumes)

@app.route('/resume')
def use_template():
    file = request.args.get('file')
    name = request.args.get('name')

    if not file:
        return "Error: Missing 'file' parameter in URL", 400

    filepath = os.path.join('static/resumes', os.path.basename(file))

    if not os.path.exists(filepath):
        return "Resume file not found.", 404

    # Dummy resume list just as example
    resumes = [
        { 'name': 'Modern Resume', 'file': 'resume1.pdf', 'url': 'static/resumes/resume1.png' },
        ...
    ]

    return render_template('resume.html', name=name, file=file, resumes=resumes)


@app.route('/transparency')
def transparency():
    return render_template("transparency.html")


@app.route('/feature/8', methods=['GET', 'POST'])
def project_ideas():
    ideas = []
    if request.method == 'POST':
        skills = request.form.get('skills')
        if skills:
            prompt = f"Suggest 5 innovative and practical project ideas for a student with these skills: {skills}. Include a short title and one-line description."
            ideas = gemini_response(prompt)  # from your gemini.py
            # Parse if necessary into [{'title': ..., 'description': ...}]
    return render_template('project_ideas.html', ideas=ideas)


@app.route('/analyze-description', methods=['POST'])
def analyze_description():
    data = request.get_json()
    description = data.get('description', '').strip()

    if not description:
        return jsonify({'message': 'Empty description'}), 400

    try:
        # Directly get AI suggestion/feedback
        ai_response = get_ai_suggestion_response(f"Here is a job description:\n\n{description}\n\nPlease analyze this for resume tailoring.")
        return jsonify({'message': ai_response}), 200
    except Exception as e:
        return jsonify({'message': f"AI Error: {str(e)}"}), 500


@app.route('/feature/<int:feature_id>')
def feature_info(feature_id):
    if not last_resume_text:
        return redirect(url_for('home'))

    feature_map = {
        1: "ATS Checker",
        2: "Formatting Feedback",
        3: "Skill Detection",
        4: "AI Suggestions",
        5: "Project Ideas",
        6: "Free Start",
        7: "Data-Driven",
        8: "Transparency"
    }
    selected_feature = feature_map.get(feature_id, "Unknown Feature")

    return render_template("feature.html", feature=selected_feature, analysis=analysis)


if __name__ == '__main__':
    app.run(debug=True)
