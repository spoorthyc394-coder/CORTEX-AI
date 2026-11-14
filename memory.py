
import sqlite3

DATABASE = "cortex_memory.db"


# Create the memory database
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


# Save information permanently
def save_memory(key, value):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO memories (key, value)
        VALUES (?, ?)
    """, (key, value))

    connection.commit()
    connection.close()


# Retrieve saved information
def get_memory(key):
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT value FROM memories WHERE key = ?",
        (key,)
    )

    result = cursor.fetchone()
    connection.close()

    if result:
        return result[0]

    return None


# Display all saved information
def show_all_memories():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("SELECT key, value FROM memories")
    results = cursor.fetchall()

    connection.close()

    return results


# Create database when this file is run
if __name__ == "__main__":
    create_database()

    print("CORTEX memory database is ready!")

    save_memory("name", "Spoorthy")
    save_memory("course", "Computer Science Engineering")

    print("\nSaved memories:")

    for key, value in show_all_memories():
        print(key, ":", value)

    print("\nRetrieved name:", get_memory("name"))
