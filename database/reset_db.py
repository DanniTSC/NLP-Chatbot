import sqlite3

DB_PATH = "chatbot.db"

def delete_non_demo_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conversations
        WHERE session_id NOT LIKE 'demo%'
    """)

    conn.commit()

    deleted_rows = cursor.rowcount

    conn.close()

    print(f"Deleted {deleted_rows} rows.")

if __name__ == "__main__":
    delete_non_demo_sessions()