from flask import Flask, request, jsonify, send_from_directory, abort
from dotenv import load_dotenv
import os
import openai
import json
from datetime import datetime
import html
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key
client = OpenAI(api_key=api_key)

app = Flask(__name__)

CHAT_DIR = "chats"
os.makedirs(CHAT_DIR, exist_ok=True)

# --- Utility: Save a message to a session file ---
def save_to_session(session_id, role, content):
    # Escape user input but NOT assistant markdown
    sanitized_content = html.escape(content) if role == "user" else content
    path = os.path.join(CHAT_DIR, f"{session_id}.json")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            chat = json.load(f)
    else:
        chat = []

    chat.append({"role": role, "content": sanitized_content})

    with open(path, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, ensure_ascii=False)

# --- Utility: Load messages from session file ---
def load_session(session_id):
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# --- Create a new session file ---
@app.route("/session/new", methods=["POST"])
def new_session():
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    return jsonify({"status": "created", "session_id": session_id}), 200

# --- Handle chat input/output ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    session_id = data.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
    model = data.get("model", "gpt-4")

    messages = load_session(session_id)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        reply = response.choices[0].message.content.strip()

        # Save messages
        save_to_session(session_id, "user", prompt)
        save_to_session(session_id, "assistant", reply)

        return jsonify({"response": reply, "session_id": session_id})

    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"error": "API request failed", "details": str(e)}), 500

# --- Return a list of available session IDs ---
@app.route("/sessions", methods=["GET"])
def get_sessions():
    files = [f.replace(".json", "") for f in os.listdir(CHAT_DIR) if f.endswith(".json")]
    return jsonify(sorted(files, reverse=True))

# --- Load specific session by ID ---
@app.route("/session/<session_id>", methods=["GET"])
def get_session(session_id):
    return jsonify(load_session(session_id))

# --- Delete a session ---
@app.route("/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"success": True})
    return abort(404, "Session not found")

# --- Rename a session ---
@app.route("/rename-session", methods=["POST"])
def rename_session():
    data = request.get_json()
    old_id = data.get("old_id")
    new_id = data.get("new_id")

    old_path = os.path.join(CHAT_DIR, f"{old_id}.json")
    new_path = os.path.join(CHAT_DIR, f"{new_id}.json")

    if not os.path.exists(old_path):
        return abort(404, "Original session not found")
    if os.path.exists(new_path):
        return abort(400, "Target session name already exists")

    os.rename(old_path, new_path)
    return jsonify({"success": True})

# --- Serve static front-end file ---
@app.route("/")
def home():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    app.run(debug=True)
