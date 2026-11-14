
import json
import sqlite3
import urllib.request
import urllib.error

# ==========================================
# CORTEX AI CONFIGURATION
# ==========================================

MODEL = "qwen3:1.7b"
OLLAMA_URL = "http://localhost:11434/api/chat"
DATABASE = "cortex_memory.db"


# ==========================================
# DATABASE AND MEMORY FUNCTIONS
# ==========================================

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


def save_memory(key, value):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO memories (key, value)
        VALUES (?, ?)
    """, (key, value))

    connection.commit()
    connection.close()


def get_all_memories():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("SELECT key, value FROM memories")
    results = cursor.fetchall()

    connection.close()
    return results


def delete_memory(key):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM memories WHERE key = ?",
        (key,)
    )

    deleted = cursor.rowcount

    connection.commit()
    connection.close()

    return deleted > 0


def search_memory(keyword):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT key, value FROM memories
        WHERE key LIKE ? OR value LIKE ?
    """, (f"%{keyword}%", f"%{keyword}%"))

    results = cursor.fetchall()

    connection.close()
    return results


# ==========================================
# AI RESPONSE FUNCTION
# ==========================================

messages = []


def ask_cortex(question):

    memories = get_all_memories()

    memory_text = "\n".join(
        f"{key}: {value}" for key, value in memories
    )

    system_message = {
        "role": "system",
        "content": (
            "You are CORTEX, a friendly personal AI assistant. "
            "Help with programming, education, technology and everyday questions. "
            "Give clear and beginner-friendly explanations. "
            "Use the user's saved memories when relevant. "
            "Never invent personal information.\n\n"
            "Saved user information:\n" + (memory_text or "No saved memories.")
        )
    }

    current_messages = [system_message] + messages[-10:]

    current_messages.append({
        "role": "user",
        "content": question
    })

    data = {
        "model": MODEL,
        "messages": current_messages,
        "stream": False
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = result["message"]["content"]

    messages.append({
        "role": "user",
        "content": question
    })

    messages.append({
        "role": "assistant",
        "content": answer
    })

    return answer


# ==========================================
# MEMORY COMMAND HANDLER
# ==========================================

def handle_memory_command(question):

    text = question.strip()
    lower_text = text.lower()

    # Save any information using:
    # remember my <key> is <value>

    if lower_text.startswith("remember my ") and " is " in lower_text:

        position = lower_text.find(" is ")

        key = text[len("remember my "):position].strip().lower()
        value = text[position + len(" is "):].strip()

        if key and value:
            save_memory(key, value)
            print(f"CORTEX: I saved your {key}: {value}")
        else:
            print("CORTEX: Please provide both the information name and value.")

        return True

    # Display all saved memories

    if lower_text in ["show memory", "show memories"]:

        memories = get_all_memories()

        if memories:
            print("\nCORTEX: Here is what I remember:")

            for key, value in memories:
                print(f"- {key}: {value}")
        else:
            print("CORTEX: My memory is empty.")

        return True

    # Search saved memories

    if lower_text.startswith("find memory "):

        keyword = text[len("find memory "):].strip()
        results = search_memory(keyword)

        if results:
            print("\nCORTEX: I found these memories:")

            for key, value in results:
                print(f"- {key}: {value}")
        else:
            print("CORTEX: I couldn't find matching information.")

        return True

    # Delete a saved memory

    if lower_text.startswith("forget my "):

        key = text[len("forget my "):].strip().lower()

        if delete_memory(key):
            print(f"CORTEX: I deleted your saved {key}.")
        else:
            print(f"CORTEX: I couldn't find a saved memory called {key}.")

        return True

    return False


# ==========================================
# MAIN CORTEX PROGRAM
# ==========================================

def main():

    create_database()

    print("=" * 50)
    print("             CORTEX AI ASSISTANT")
    print("=" * 50)

    print("AI Model: Qwen3 1.7B")
    print("Memory: SQLite 2.0")
    print("Status: Ready")

    print("\nAvailable commands:")
    print("1. remember my <topic> is <information>")
    print("2. show memory")
    print("3. find memory <keyword>")
    print("4. forget my <topic>")
    print("5. exit")

    print("=" * 50)

    while True:

        question = input("\nYou: ").strip()

        if not question:
            print("CORTEX: Please enter a message.")
            continue

        if question.lower() in ["exit", "quit", "bye"]:
            print("CORTEX: Goodbye! See you again.")
            break

        # Process memory commands first

        if handle_memory_command(question):
            continue

        # Send other questions to the AI model

        try:
            print("\nCORTEX: Thinking...")

            answer = ask_cortex(question)

            print("\nCORTEX:", answer)

        except urllib.error.URLError:
            print("\nCORTEX: Cannot connect to Ollama.")
            print("Please check whether Ollama is running.")

        except Exception as error:
            print("\nCORTEX: An error occurred:", error)


# ==========================================
# START PROGRAM
# ==========================================

if __name__ == "__main__":
    main()
