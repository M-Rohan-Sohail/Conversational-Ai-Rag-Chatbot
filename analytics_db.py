import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "analytics.db")

def init_analytics_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        query_type TEXT NOT NULL,
        query_text TEXT,
        response_text TEXT,
        was_answered BOOLEAN
    )
    ''')
    try:
        cursor.execute("ALTER TABLE queries ADD COLUMN latency REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def log_query(query_type, query_text, response_text, was_answered, latency=0.0):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO queries (query_type, query_text, response_text, was_answered, latency)
        VALUES (?, ?, ?, ?, ?)
        ''', (query_type, query_text, response_text, was_answered, latency))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log analytics: {e}")

def get_analytics():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM queries")
        total_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM queries WHERE query_type = 'text'")
        text_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM queries WHERE query_type = 'audio'")
        voice_queries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM queries WHERE was_answered = 0")
        unanswered_queries = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total_queries": total_queries,
            "text_queries": text_queries,
            "voice_queries": voice_queries,
            "unanswered_queries": unanswered_queries
        }
    except Exception as e:
        print(f"Failed to fetch analytics: {e}")
        return {
            "total_queries": 0,
            "text_queries": 0,
            "voice_queries": 0,
            "unanswered_queries": 0
        }

if __name__ == "__main__":
    init_analytics_db()
    print("Analytics DB initialized.")

def get_recent_queries(limit=30):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT query_text, response_text, latency, query_type
        FROM queries
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return [{"query": r[0], "answer": r[1], "latency": r[2], "type": r[3]} for r in results]
    except Exception as e:
        print(f"Failed to fetch recent queries: {e}")
        return []
