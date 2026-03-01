from flask import Flask, session, request, jsonify, render_template
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------------------------------------------------------
# 1. FINALIZED MOCK DATA (4 Choices per Question)
# ---------------------------------------------------------
MOCK_QUESTIONS = {
    "personality": [
        {
            "q": "When faced with an unexpected change in plans, you usually:",
            "opts": ["A. Feel anxious / Stick to plan", "B. Accept calmly / Adjust", "C. Improve the new plan", "D. Lead and innovate"],
            "w": [{"Conscientiousness": 2}, {"Emotional_Stability": 2}, {"Openness": 2}, {"Extraversion": 2}]
        },
        {
            "q": "In group settings, your usual role is:",
            "opts": ["A. Observing / Analyzing", "B. Supporting / Harmony", "C. Offering ideas proactively", "D. Taking charge / Guiding"],
            "w": [{"Introversion": 2}, {"Agreeableness": 2}, {"Openness": 2}, {"Extraversion": 2}]
        }
    ],
    "behavior": [
        {
            "q": "A teammate misses an important deadline. You:",
            "opts": ["A. Ignore it", "B. Help without asking", "C. Discuss / Find solution", "D. Escalate to manager"],
            "w": [{"Passive": 1}, {"Supportive": 2}, {"Leadership": 2}, {"Authority": 1}]
        },
        {
            "q": "You notice a workflow in your team is inefficient. You:",
            "opts": ["A. Continue as usual", "B. Suggest minor tweaks", "C. Research / Propose system", "D. Lead a full overhaul"],
            "w": [{"Stability": 1}, {"Improvement": 1}, {"Analytical": 2}, {"Initiative": 3}]
        }
    ],
    "skills": [
        {
            "q": "If 5 machines take 5 hours to produce 5 items, how long will 10 machines take to produce 10 items?",
            "opts": ["A. 2.5 hours", "B. 5 hours", "C. 10 hours", "D. 20 hours"],
            "w": [{"Logic_Error": 0}, {"Logic_Success": 3}, {"Logic_Error": 0}, {"Logic_Error": 0}]
        },
        {
            "q": "Find the next number in the series: 2, 6, 12, 20, …",
            "opts": ["A. 24", "B. 30", "C. 28", "D. 36"],
            "w": [{"Logic_Error": 0}, {"Logic_Success": 3}, {"Logic_Error": 0}, {"Logic_Error": 0}]
        }
    ],
    "market": [
        {
            "q": "Which industry is seeing rapid growth due to AI and automation?",
            "opts": ["A. Print media", "B. Renewable / Green tech", "C. Coal mining", "D. Manual bookkeeping"],
            "w": [{"Market_Awareness": 0}, {"Market_Awareness": 3}, {"Market_Awareness": 0}, {"Market_Awareness": 0}]
        },
        {
            "q": "To remain competitive in 5 years, a company should:",
            "opts": ["A. Stick to past methods", "B. Focus on cost-cutting", "C. Invest in tech / Upskilling", "D. Reduce R&D"],
            "w": [{"Strategy": 0}, {"Strategy": 1}, {"Strategy": 3}, {"Strategy": 0}]
        }
    ]
}

def get_phase_info(step):
    if step <= 2: return "personality", "#4CAF50"
    if step <= 4: return "behavior", "#2196F3"
    if step <= 6: return "skills", "#FF9800"
    if step <= 8: return "market", "#9C27B0"
    return "end", "#333"

def build_scenario_response():
    step = session.get('current_node', 1)
    phase_name, phase_color = get_phase_info(step)
    if phase_name == "end":
        return jsonify({"end": True, "final_profile": session.get('user_profile')})
    
    local_idx = (step - 1) % 2 
    question_data = MOCK_QUESTIONS[phase_name][local_idx]
    return jsonify({
        "node_id": step,
        "phase": phase_name.upper(),
        "color": phase_color,
        "question": question_data['q'],
        "choices": question_data['opts'],
        "trait_summary": session.get('user_profile')
    })

@app.route('/')
def index(): return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    session['current_node'] = 1
    session['user_profile'] = {"personality": {}, "behavior": {}, "skills": {}, "market": {}}
    session.modified = True
    return build_scenario_response()

@app.route('/next', methods=['POST'])
def next_node():
    data = request.get_json()
    choice_idx = data.get('choice_index', 0)
    current_step = session.get('current_node', 1)
    phase_name, _ = get_phase_info(current_step)
    
    if phase_name != "end":
        local_idx = (current_step - 1) % 2
        question_data = MOCK_QUESTIONS[phase_name][local_idx]
        selected_weight = question_data['w'][choice_idx]
        profile = session.get('user_profile')
        for trait, val in selected_weight.items():
            profile[phase_name][trait] = profile[phase_name].get(trait, 0) + val
        session['user_profile'] = profile
        session['current_node'] = current_step + 1
        session.modified = True
    return build_scenario_response()

if __name__ == "__main__":
    app.run(debug=True, port=5000)