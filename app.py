from flask import Flask, session, request, jsonify, render_template
import os
import json
import re
from dotenv import load_dotenv
from google import genai # Modern 2026 Import

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv()

# Initialize the Client with the key from .env
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------
# AI RECOGNITION ENGINE
# ---------------------------------------------------------
def get_ai_recommendation(journal, profile):
    # Use the 2026 workhorse model we verified
    model_id = 'gemini-2.5-flash-lite'
    
    transcript = "\n".join([f"Q: {j['question']} | A: {j['user_answer']}" for j in journal])
    
# NEW PROMPT LOGIC

    # NEW PROMPT LOGIC
    prompt = f"""
    Analyze this career journey:
    TRANSCRIPT: {transcript}
    SCORES: {profile}

    OUTPUT RULES:
    1. Return ONLY a valid JSON object.
    2. "title": The primary 2026 career match.
    3. "match_reason": 2 sentences explaining why.
    4. "alternatives": A list of 3 other high-match career titles (Close Paths).
    
    REQUIRED JSON FORMAT:
    {{
      "title": "Primary Career",
      "match_reason": "Explanation...",
      "alternatives": ["Alternative 1", "Alternative 2", "Alternative 3"]
    }}
    """
    
    try:
        response = client.models.generate_content(model=model_id, contents=prompt)
        # Clean markdown if present (SDK types .text as optional)
        text = response.text or ""
        clean_json = re.sub(r"```json|```", "", text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return {
            "title": "Zenith Explorer",
            "match_reason": "The Oracle is calibrating. You are a versatile pioneer.",
            "pathway": ["Adaptability", "Tech Literacy", "Problem Solving"],
            "vibe": "Versatile, Resilient, Ready"
        }

# ---------------------------------------------------------
# UI & PHASE CONTROLLER
# ---------------------------------------------------------
def load_questions():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)['questions']

def get_phase_info(step):
    if step <= 5: return "OCEAN", "#4CAF50"
    if step <= 11: return "RIASEC", "#2196F3"
    if step <= 16: return "SJT", "#FF9800"
    return "end", "#333"

def build_scenario_response():
    step = session.get('current_node', 1)
    phase_name, phase_color = get_phase_info(step)
    
    # CRITICAL CHANGE: If end of journey, call the AI!
    if phase_name == "end":
        journal = session.get('ai_journal', [])
        profile = session.get('user_profile', {})
        
        # Get the real AI result
        ai_result = get_ai_recommendation(journal, profile)
        
        return jsonify({
            "end": True, 
            "ai_result": ai_result,
            "trait_summary": profile
        })
    
    questions = load_questions()
    q_data = next((q for q in questions if q['id'] == step), None)
    if q_data is None:
        return jsonify({"error": "unknown_question", "step": step}), 404
    
    return jsonify({
        "node_id": step,
        "phase": q_data['phase'],
        "type": q_data['type'],
        "color": phase_color,
        "question": q_data['q'],
        "choices": q_data.get('opts', []),
        "trait_summary": session.get('user_profile')
    })

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    session['current_node'] = 1
    session['user_profile'] = {"ocean": {}, "riasec": {}, "sjt": {}}
    session['ai_journal'] = []
    session.modified = True
    return build_scenario_response()

@app.route('/next', methods=['POST'])
def next_node():
    data = request.get_json()
    choice_idx = data.get('choice_index') 
    current_step = session.get('current_node', 1)
    
    questions = load_questions()
    q_data = next((q for q in questions if q['id'] == current_step), None)
    
    if q_data:
        # Journaling Logic
        labels = ["Strongly Disagree", "Disagree", "Somewhat Disagree", "Neutral", "Somewhat Agree", "Agree", "Strongly Agree"]
        user_answer_text = labels[choice_idx - 1] if q_data['type'] == "likert" else q_data['opts'][choice_idx]

        journal = session.get('ai_journal', [])
        journal.append({
            "step": current_step,
            "phase": q_data['phase'],
            "trait": q_data['trait'],
            "question": q_data['q'],
            "user_answer": user_answer_text
        })
        session['ai_journal'] = journal

        # Scoring Logic
        score = choice_idx if q_data['type'] == "likert" else (choice_idx + 1)
        if q_data.get('reverse') and q_data['type'] == "likert":
            score = 8 - choice_idx

        profile = session.get('user_profile')
        if profile is None:
            return jsonify({"error": "session_not_initialized"}), 400
        phase_key = q_data['phase'].lower()
        trait_key = q_data['trait']
        profile[phase_key][trait_key] = profile[phase_key].get(trait_key, 0) + score
        
        session['user_profile'] = profile
        session['current_node'] = current_step + 1
        session.modified = True
        
    return build_scenario_response()

if __name__ == "__main__":
    app.run(debug=True, port=5000)