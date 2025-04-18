from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import openai
import json
from datetime import datetime

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

app = Flask(__name__)

CHAT_DIR = "chats"
os.makedirs(CHAT_DIR, exist_ok=True)

# --- Utility: Save a message to a session file ---
def save_to_session(session_id, role, content):
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            chat = json.load(f)
    else:
        chat = []
    chat.append({"role": role, "content": content})
    with open(path, "w") as f:
        json.dump(chat, f, indent=2)

# --- Utility: Load messages from session file ---
def load_session(session_id):
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

# ✅ NEW: Create a new session file with an empty chat list
@app.route("/session/new", methods=["POST"])
def new_session():
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f, indent=2)

    return jsonify({"status": "created", "session_id": session_id}), 200

# --- Handle chat input/output ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    session_id = data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))

    messages = load_session(session_id)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        print("OpenAI response:", response)

        # ✅ Get the assistant's message properly
        if hasattr(response, 'choices') and len(response.choices) > 0:
            reply = response.choices[0].message.content.strip()
        else:
            raise ValueError("No valid response from OpenAI.")

        # Save both user and assistant messages
        save_to_session(session_id, "user", prompt)
        save_to_session(session_id, "assistant", reply)

        return jsonify({"response": reply, "session_id": session_id})

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"error": "API request failed", "details": str(e)}), 500

# --- Return a list of available session IDs ---
@app.route("/sessions", methods=["GET"])
def get_sessions():
    files = [f.replace(".json", "") for f in os.listdir(CHAT_DIR)]
    return jsonify(sorted(files, reverse=True))

# --- Load specific session by ID ---
@app.route("/session/<session_id>", methods=["GET"])
def get_session(session_id):
    return jsonify(load_session(session_id))

# --- Serve static front-end file ---
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    app.run(debug=True)
