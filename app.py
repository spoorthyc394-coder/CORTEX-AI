
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import urllib.request
import urllib.error
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "cortex_memory.db")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:1.7b"

conversation = []


# ------------------------------------------
# DATABASE
# ------------------------------------------

def create_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def get_memories():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("SELECT key, value FROM memories")
    memories = cursor.fetchall()

    connection.close()
    return memories


def save_memory(key, value):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO memories (key, value)
        VALUES (?, ?)
    """, (key, value))

    connection.commit()
    connection.close()


def delete_memory(key):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM memories WHERE key = ?", (key,))
    deleted = cursor.rowcount

    connection.commit()
    connection.close()
    return deleted > 0


# ------------------------------------------
# WEBSITE HOME PAGE
# ------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------------------
# AI CHAT API
# ------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}
    question = data.get("message", "").strip()

    if not question:
        return jsonify({"error": "Please enter a message."}), 400

    memories = get_memories()

    memory_text = "\n".join(
        f"{key}: {value}" for key, value in memories
    )

    system_message = {
        "role": "system",
        "content": (
            "You are CORTEX NEXUS, a friendly personal AI assistant. "
            "Help with programming, education, technology and everyday tasks. "
            "Explain things clearly and accurately. "
            "Use saved user memories when relevant. "
            "Never invent personal information.\n\n"
            "Saved memories:\n" + (memory_text or "No saved memories.")
        )
    }

    messages = [system_message] + conversation[-10:]

    messages.append({
        "role": "user",
        "content": question
    })

    payload = {
    "model": MODEL,
    "messages": messages,
    "stream": False,
    "think": False,
    "options": {
        "num_predict": 256,
        "temperature": 0.7
    }
}


    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))

        answer = result["message"]["content"]

        conversation.append({
            "role": "user",
            "content": question
        })

        conversation.append({
            "role": "assistant",
            "content": answer
        })

        return jsonify({"reply": answer})

    except urllib.error.URLError:
        return jsonify({
            "error": "Cannot connect to Ollama. Please check that Ollama is running."
        }), 503

    except Exception as error:
        app.logger.exception("AI request failed")
        return jsonify({"error": "Something went wrong: " + str(error)}), 500


# ------------------------------------------
# MEMORY API
# ------------------------------------------

@app.route("/api/memories", methods=["GET"])
def memories_list():
    return jsonify([
        {"key": key, "value": value}
        for key, value in get_memories()
    ])


@app.route("/api/memories", methods=["POST"])
def memories_save():

    data = request.get_json(silent=True) or {}

    key = data.get("key", "").strip().lower()
    value = data.get("value", "").strip()

    if not key or not value:
        return jsonify({"error": "Both fields are required."}), 400

    save_memory(key, value)

    return jsonify({"message": "Memory saved successfully!"})


@app.route("/api/memories/<key>", methods=["DELETE"])
def memories_delete(key):

    if delete_memory(key):
        return jsonify({"message": "Memory deleted successfully!"})

    return jsonify({"error": "Memory not found."}), 404


# Create database when the app starts
create_database()


# ------------------------------------------
# START WEBSITE
# ------------------------------------------

if __name__ == "__main__":

    print("CORTEX NEXUS website is starting...")
    print("Open http://127.0.0.1:5000 in your browser")

    app.run(host="0.0.0.0", port=5000, debug=True)

