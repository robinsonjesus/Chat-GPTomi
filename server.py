from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import openai
import json
from datetime import datetime


# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)  # ✅ create client with key

app = Flask(__name__)

CHAT_DIR = "chats"
os.makedirs(CHAT_DIR, exist_ok=True)

# Save a message to a session
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

# Load a session
def load_session(session_id):
    path = os.path.join(CHAT_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

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

        # Debugging: print out the full response to inspect
        print("OpenAI response:", response)

        # Correct way to access the content from the ChatCompletionMessage
        if hasattr(response, 'choices') and len(response.choices) > 0:
            reply = response.choices[0].message.content.strip()  # Use dot notation for message content
        else:
            raise ValueError("No valid response in 'choices'.")

        # Save both user input and reply
        save_to_session(session_id, "user", prompt)
        save_to_session(session_id, "assistant", reply)

        return jsonify({"response": reply, "session_id": session_id})
    
    except Exception as e:
        print("OpenAI API error:", e)
        return jsonify({"error": "API request failed", "details": str(e)}), 500




# Get all saved sessions
@app.route("/sessions", methods=["GET"])
def get_sessions():
    files = [f.replace(".json", "") for f in os.listdir(CHAT_DIR)]
    return jsonify(sorted(files, reverse=True))

# Load a specific session
@app.route("/session/<session_id>", methods=["GET"])
def get_session(session_id):
    return jsonify(load_session(session_id))

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    app.run(debug=True)
