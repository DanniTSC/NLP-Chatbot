import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().with_name("chatbot.db")

def delete_non_demo_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    session_count = cursor.execute("""
        SELECT COUNT(DISTINCT session_id)
        FROM conversations
        WHERE session_id NOT LIKE 'demo-%'
    """).fetchone()[0]
    cursor.execute("""
        DELETE FROM conversations
        WHERE session_id NOT LIKE 'demo-%'
    """)

    conn.commit()

    deleted_rows = cursor.rowcount

    conn.close()

    print(f"Deleted {deleted_rows} rows from {session_count} non-demo sessions.")

if __name__ == "__main__":
    delete_non_demo_sessions()
