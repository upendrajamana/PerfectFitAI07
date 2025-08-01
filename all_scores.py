import re
import spacy
from datetime import datetime
from dateutil import parser
from collections import defaultdict
import language_tool_python


class ResumeAnalyzer:
    def __init__(self):
        # Load spaCy model (download with: python -m spacy download en_core_web_sm)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None

        # Initialize grammar tool
        try:
            self.grammar_tool = language_tool_python.LanguageTool('en-US')
        except:
            print("Warning: LanguageTool not available. Install with: pip install language_tool_python")
            self.grammar_tool = None

        # Define patterns and keywords
        self.setup_patterns()

    def setup_patterns(self):
        """Initialize patterns and keyword lists"""

        # Unnecessary sections
        self.unnecessary_sections = [
            'objective', 'references', 'hobbies', 'interests', 'personal statement',
            'career objective', 'personal interests', 'references available upon request'
        ]

        # Strong action verbs
        self.action_verbs = [
            'achieved', 'analyzed', 'built', 'created', 'delivered', 'developed',
            'designed', 'established', 'executed', 'generated', 'improved',
            'increased', 'launched', 'led', 'managed', 'optimized', 'organized',
            'planned', 'reduced', 'streamlined', 'supervised', 'transformed',
            'accelerated', 'accomplished', 'adapted', 'administered', 'advised',
            'collaborated', 'coordinated', 'directed', 'enhanced', 'facilitated',
            'implemented', 'initiated', 'innovated', 'integrated', 'motivated',
            'negotiated', 'overcame', 'pioneered', 'resolved', 'spearheaded'
        ]

        # Generic responsibility phrases to penalize
        self.generic_phrases = [
            'responsible for', 'duties include', 'tasks involved', 'worked on',
            'helped with', 'assisted in', 'participated in', 'involved in',
            'responsible to', 'accountable for'
        ]

        # Sample keywords for different industries/roles
        self.sample_keywords = {
            'technical': [
                'python', 'java', 'javascript', 'sql', 'aws', 'docker', 'kubernetes',
                'api', 'database', 'machine learning', 'data analysis', 'git',
                'agile', 'scrum', 'ci/cd', 'testing', 'debugging'
            ],
            'business': [
                'project management', 'stakeholder', 'budget', 'roi', 'kpi',
                'strategy', 'leadership', 'team building', 'process improvement',
                'client relations', 'sales', 'revenue', 'market analysis'
            ],
            'general': [
                'communication', 'problem solving', 'analytical', 'detail oriented',
                'time management', 'multitasking', 'adaptable', 'creative',
                'collaborative', 'self-motivated'
            ]
        }

    def analyze_resume(self, resume_text):
        """Main function to analyze resume and return scores for all categories"""

        results = {}


        # 1. Quantify Impact
        results['quantify_impact'] = self.analyze_quantify_impact(resume_text)

        # 2. Unnecessary Sections
        results['unnecessary_sections'] = self.analyze_unnecessary_sections(resume_text)

        # 3. Contact Details
        results['contact_details'] = self.analyze_contact_details(resume_text)

        # 4. Date Consistency / Gaps
        results['date_consistency'] = self.analyze_date_consistency(resume_text)

        # 5. Missing Keywords
        results['keywords'] = self.analyze_keywords(resume_text)

        # 6. Action Verbs
        results['action_verbs'] = self.analyze_action_verbs(resume_text)

        # 7. Responsibilities vs Achievements
        results['achievements'] = self.analyze_achievements(resume_text)

        # 8. Grammatical Issues
        results['grammar'] = self.analyze_grammar(resume_text)
        print(results['quantify_impact']['score'])
        print(results['quantify_impact']['feedback'])
        return results

    def analyze_quantify_impact(self, text):
        """Check for numbers/metrics in bullet points"""

        # Find bullet points (lines starting with -, •, *, or numbers)
        bullet_pattern = r'^\s*[•\-\*\d]+\.?\s+(.+)$'
        bullets = re.findall(bullet_pattern, text, re.MULTILINE)

        if not bullets:
            return {
                'score': 0,
                'feedback': 'No bullet points detected. Use bullet points to highlight achievements.'
            }

        # Look for numbers, percentages, dollar amounts, time periods
        number_patterns = [
            r'\d+%',  # percentages
            r'\$[\d,]+',  # dollar amounts
            r'\d+[kmb]',  # abbreviated numbers (5k, 2m, 1b)
            r'\d+\+',  # numbers with plus
            r'\d+x',  # multipliers
            r'\d+:\d+',  # ratios
            r'\d+\s*(hours?|days?|weeks?|months?|years?)',  # time periods
            r'\d{1,3}(,\d{3})*',  # large numbers with commas
            r'\b\d+\b'  # any standalone numbers
        ]

        quantified_bullets = 0
        for bullet in bullets:
            has_number = any(re.search(pattern, bullet, re.IGNORECASE) for pattern in number_patterns)
            if has_number:
                quantified_bullets += 1

        score = min(100, int((quantified_bullets / len(bullets)) * 100))

        # Identify which bullets lack quantification for specific feedback
        unquantified_examples = []
        for bullet in bullets[:3]:  # Show first 3 examples
            has_number = any(re.search(pattern, bullet, re.IGNORECASE) for pattern in number_patterns)
            if not has_number:
                unquantified_examples.append(bullet[:60] + "..." if len(bullet) > 60 else bullet)

        if score >= 90:
            feedback = f"Excellent quantification! {quantified_bullets}/{len(bullets)} bullets include metrics. Your resume shows measurable impact."
        elif score >= 70:
            feedback = f"Good use of numbers ({quantified_bullets}/{len(bullets)} bullets). To improve: Add specific metrics like '25% increase', '$50K savings', or '3-month timeline' to remaining bullets."
        elif score >= 50:
            feedback = f"Moderate quantification ({quantified_bullets}/{len(bullets)} bullets). Transform vague statements into numbers. Example improvements needed:"
            if unquantified_examples:
                feedback += f"\n- '{unquantified_examples[0]}' → Add percentages, dollar amounts, or timeframes"
        else:
            feedback = f"Weak quantification ({quantified_bullets}/{len(bullets)} bullets). Most bullets lack impact metrics. Examples to fix:"
            for i, example in enumerate(unquantified_examples[:2]):
                feedback += f"\n- '{example}' → Specify: How much? How many? What % improvement?"

        return {'score': score, 'feedback': feedback}

    def analyze_unnecessary_sections(self, text):
        """Flag unnecessary sections"""

        text_lower = text.lower()
        found_sections = []

        for section in self.unnecessary_sections:
            if section in text_lower:
                found_sections.append(section.title())

        if not found_sections:
            return {
                'score': 100,
                'feedback': 'Perfect! No space-wasting sections found. Your resume focuses on relevant content.'
            }

        # Deduct points based on number of unnecessary sections
        penalty = min(80, len(found_sections) * 25)
        score = max(20, 100 - penalty)

        sections_list = ', '.join(found_sections)
        feedback = f"Remove these sections to save space: {sections_list}. Replace with:"
        if 'objective' in [s.lower() for s in found_sections]:
            feedback += "\n- Instead of 'Objective': Use a professional summary with specific achievements"
        if any(ref in [s.lower() for s in found_sections] for ref in ['references', 'references available']):
            feedback += "\n- Instead of 'References': Add more work experience or technical skills"
        if any(hobby in [s.lower() for s in found_sections] for hobby in ['hobbies', 'interests']):
            feedback += "\n- Instead of 'Hobbies': Include relevant certifications or volunteer work"

        return {'score': score, 'feedback': feedback}

    def analyze_contact_details(self, text):
        """Check for email, phone, LinkedIn/GitHub"""

        contact_items = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'linkedin': r'linkedin\.com/in/[\w-]+',
            'github': r'github\.com/[\w-]+'
        }

        found_items = []
        missing_items = []

        for item, pattern in contact_items.items():
            if re.search(pattern, text, re.IGNORECASE):
                found_items.append(item)
            else:
                missing_items.append(item)

        score = int((len(found_items) / len(contact_items)) * 100)

        if score == 100:
            feedback = "Perfect contact section! All essential details are easily found by recruiters."
        elif score >= 75:
            missing_list = ', '.join(missing_items)
            feedback = f"Good contact info. Missing: {missing_list}. "
            if 'linkedin' in missing_items:
                feedback += "Add LinkedIn profile - 87% of recruiters use it for candidate research. "
            if 'github' in missing_items:
                feedback += "Add GitHub profile to showcase your code and projects."
        elif score >= 50:
            feedback = f"Incomplete contact details. Add: {', '.join(missing_items)}. "
            feedback += "Make it easy for employers to reach you - missing contact info costs opportunities."
        else:
            feedback = f"Critical contact info missing: {', '.join(missing_items)}. "
            feedback += "Add these immediately - resumes without proper contact details are often discarded."

        return {'score': score, 'feedback': feedback}

    def analyze_date_consistency(self, text):
        """Extract dates and check for gaps"""

        # Common date patterns
        date_patterns = [
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',
            r'\b\d{1,2}/\d{4}\b',
            r'\b\d{4}\s*-\s*\d{4}\b',
            r'\b\d{4}\s*–\s*\d{4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b'
        ]

        all_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_dates.extend(matches)

        if len(all_dates) < 2:
            return {
                'score': 50,
                'feedback': 'Not enough date information to analyze gaps. Include start/end dates for positions.'
            }

        # For simplicity, assume dates are in chronological order and look for obvious gaps
        # This is a basic implementation - could be enhanced with more sophisticated date parsing

        gap_indicators = [
            'gap', 'break', 'sabbatical', 'unemployed', 'freelance',
            'between positions', 'career break'
        ]

        has_gap_indicators = any(indicator in text.lower() for indicator in gap_indicators)

        # Basic scoring - could be improved with actual date parsing
        if has_gap_indicators:
            score = 60
            feedback = "Employment gaps detected. Solutions: 1) Add freelance/consulting work during gaps, 2) Include relevant volunteer experience, 3) Mention professional development (courses, certifications), 4) Consider functional resume format to de-emphasize gaps."
        else:
            # Check for potential formatting issues with dates
            date_issues = []
            if re.search(r'\d{4}\s*-\s*\d{4}', text) and re.search(r'[A-Za-z]{3}\s+\d{4}', text):
                date_issues.append("Mixed date formats detected")

            if date_issues:
                score = 75
                feedback = f"Date formatting needs consistency. Issues: {', '.join(date_issues)}. Use consistent format like 'Jan 2020 - Dec 2022' throughout."
            else:
                score = 85
                feedback = "Good date consistency. Ensure all positions show clear start/end dates. If currently employed, use 'Present' instead of end date."

        return {'score': score, 'feedback': feedback}

    def analyze_keywords(self, text):
        """Compare resume text with keyword lists"""

        text_lower = text.lower()
        all_keywords = []

        # Combine all keyword categories
        for category, keywords in self.sample_keywords.items():
            all_keywords.extend(keywords)

        found_keywords = []
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)

        # Remove duplicates
        found_keywords = list(set(found_keywords))

        # Score based on percentage of keywords found
        keyword_coverage = len(found_keywords) / len(all_keywords)
        score = min(100, int(keyword_coverage * 150))  # Boost score since perfect match is unlikely

        if score >= 80:
            feedback = f"Excellent keyword coverage! Found {len(found_keywords)} relevant keywords."
        elif score >= 60:
            feedback = f"Good keyword presence. Found {len(found_keywords)} keywords. Consider adding more industry-specific terms."
        elif score >= 40:
            feedback = f"Moderate keyword usage. Found {len(found_keywords)} keywords. Add more technical and soft skills."
        else:
            feedback = f"Low keyword coverage. Only {len(found_keywords)} keywords found. Research job descriptions and add relevant skills."

        return {'score': score, 'feedback': feedback}

    def analyze_action_verbs(self, text):
        """Score bullet points that start with action verbs"""

        # Find bullet points
        bullet_pattern = r'^\s*[•\-\*\d]+\.?\s+(.+)$'
        bullets = re.findall(bullet_pattern, text, re.MULTILINE)

        if not bullets:
            return {
                'score': 0,
                'feedback': 'No bullet points found. Use bullet points starting with strong action verbs.'
            }

        action_verb_bullets = 0
        for bullet in bullets:
            first_word = bullet.split()[0].lower() if bullet.split() else ''
            if first_word in self.action_verbs:
                action_verb_bullets += 1

        score = min(100, int((action_verb_bullets / len(bullets)) * 100))

        if score >= 80:
            feedback = f"Excellent! {action_verb_bullets}/{len(bullets)} bullet points start with strong action verbs."
        elif score >= 60:
            feedback = f"Good use of action verbs. {action_verb_bullets}/{len(bullets)} bullets start with strong verbs. Try to improve more."
        elif score >= 40:
            feedback = f"Some action verbs used. {action_verb_bullets}/{len(bullets)} bullets start with action verbs. Replace weak starts with power verbs."
        else:
            feedback = f"Weak action verb usage. Only {action_verb_bullets}/{len(bullets)} bullets start with action verbs. Begin bullets with achieved, developed, led, etc."

        return {'score': score, 'feedback': feedback}

    def analyze_achievements(self, text):
        """Detect generic phrases vs measurable results"""

        text_lower = text.lower()

        # Count generic responsibility phrases
        generic_count = 0
        for phrase in self.generic_phrases:
            generic_count += len(re.findall(phrase, text_lower))

        # Count achievement indicators
        achievement_patterns = [
            r'increased.*\d+%',
            r'decreased.*\d+%',
            r'improved.*\d+%',
            r'reduced.*\d+%',
            r'achieved.*\d+',
            r'exceeded.*\d+',
            r'generated.*\$',
            r'saved.*\$',
            r'delivered.*ahead of schedule',
            r'under budget',
            r'recognition',
            r'award',
            r'promoted'
        ]

        achievement_count = 0
        for pattern in achievement_patterns:
            achievement_count += len(re.findall(pattern, text_lower))

        # Calculate score
        total_phrases = generic_count + achievement_count
        if total_phrases == 0:
            score = 50
            feedback = "Add more specific examples of your achievements and impact."
        else:
            achievement_ratio = achievement_count / total_phrases
            score = min(100, int(achievement_ratio * 100))

            if score >= 80:
                feedback = f"Excellent focus on achievements! High ratio of results-oriented content."
            elif score >= 60:
                feedback = f"Good balance. Consider replacing some responsibility statements with specific achievements."
            elif score >= 40:
                feedback = f"Mix of responsibilities and achievements. Focus more on 'what you accomplished' vs 'what you did'."
            else:
                feedback = f"Too many generic responsibility statements. Rewrite to show specific results and impact."

        return {'score': score, 'feedback': feedback}

    def analyze_grammar(self, text):
        """Check grammar using language_tool_python"""

        if not self.grammar_tool:
            return {
                'score': 75,
                'feedback': 'Grammar check unavailable. Please manually proofread for errors.'
            }

        try:
            matches = self.grammar_tool.check(text)
            error_count = len(matches)

            # Score based on error density (errors per 100 words)
            word_count = len(text.split())
            if word_count == 0:
                return {'score': 0, 'feedback': 'No text to analyze.'}

            error_density = (error_count / word_count) * 100

            if error_density <= 1:
                score = 100
                feedback = f"Excellent! Only {error_count} grammatical issues found."
            elif error_density <= 2:
                score = 85
                feedback = f"Good grammar. {error_count} minor issues detected. Review and correct."
            elif error_density <= 4:
                score = 70
                feedback = f"Several grammatical issues found ({error_count}). Careful proofreading needed."
            else:
                score = 50
                feedback = f"Many grammatical errors detected ({error_count}). Consider professional proofreading."

            return {'score': score, 'feedback': feedback}

        except Exception as e:
            return {
                'score': 75,
                'feedback': f'Grammar check error. Please manually proofread.'
            }


# Example usage function
def analyze_sample_resume():
    """Example function showing how to use the analyzer"""

    sample_resume = """
    John Doe
    john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe | github.com/johndoe

    Experience:

    Software Engineer | ABC Company | Jan 2020 - Present
    • Developed 5 web applications using Python and JavaScript, increasing user engagement by 40%
    • Led a team of 3 developers to deliver projects 2 weeks ahead of schedule
    • Reduced database query time by 60% through optimization techniques
    • Implemented CI/CD pipeline that decreased deployment time from 2 hours to 15 minutes

    Junior Developer | XYZ Corp | Jun 2018 - Dec 2019
    • Responsible for maintaining legacy systems
    • Worked on bug fixes and minor enhancements
    • Participated in code reviews and team meetings

    Skills:
    Python, JavaScript, SQL, AWS, Docker, Git, Agile, Problem Solving, Team Leadership

    Education:
    B.S. Computer Science | State University | 2018
    """

    analyzer = ResumeAnalyzer()
    results = analyzer.analyze_resume(sample_resume)

    print("Resume Analysis Results:")
    print("=" * 50)

    for category, result in results.items():
        print(f"\n{category.replace('_', ' ').title()}:")
        print(f"Score: {result['score']}/100")
        print(f"Feedback: {result['feedback']}")


if __name__ == "__main__":
    # Run the example
    analyze_sample_resume()
