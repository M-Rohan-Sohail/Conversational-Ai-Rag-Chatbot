import sqlite3
import os
import re
from llm_openai import generate_llm_response

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_data")

# ============================================================
# SECURITY: Dangerous SQL keywords that must NEVER be executed
# ============================================================
BLOCKED_SQL_KEYWORDS = [
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
    "REPLACE", "TRUNCATE", "RENAME", "GRANT", "REVOKE",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
    "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT",
    "EXEC", "EXECUTE", "--", "/*", "*/", ";"
]


def validate_sql(sql_query):
    if not sql_query or not sql_query.strip():
        return False, "Empty SQL query."

    normalized = sql_query.strip().upper()

    if not normalized.startswith("SELECT"):
        return False, f"Blocked: Only SELECT queries are allowed. Got: {sql_query[:50]}"

    for keyword in BLOCKED_SQL_KEYWORDS:
        if keyword in ("--", "/*", "*/", ";"):
            if keyword in sql_query:
                return False, f"Blocked: Dangerous character sequence '{keyword}' detected."
        else:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, normalized):
                return False, f"Blocked: Dangerous SQL keyword '{keyword}' detected."

    cleaned = re.sub(r"'[^']*'", "", sql_query)
    if ";" in cleaned:
        return False, "Blocked: Multiple SQL statements are not allowed."

    return True, "Query is safe."

def get_sql_files():
    if not os.path.exists(UPLOAD_DIR):
        return []
    return [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".db") or f.endswith(".sqlite")]

def extract_schemas():
    """Extract schemas from all uploaded SQL files."""
    schemas = []
    sql_files = get_sql_files()
    if not sql_files:
        return "No databases available."
        
    for i, file in enumerate(sql_files):
        file_path = os.path.join(UPLOAD_DIR, file)
        db_name = f"db_{i}"
        
        try:
            # Open in read-only mode for safety
            conn = sqlite3.connect(f"file:{file_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema_info = f"Database: {file} (Alias: {db_name})\n"
            for table_name, sql in tables:
                schema_info += f"- Table: {table_name}\n  Schema: {sql}\n"
            schemas.append(schema_info)
            conn.close()
        except Exception as e:
            schemas.append(f"Failed to read schema for {file}: {e}")
            
    return "\n".join(schemas)

def generate_sql(user_query):
    schema_info = extract_schemas()
    if schema_info == "No databases available.":
        return "SELECT 'Query not applicable' AS result"
        
    system_prompt = f"""
    You are a SQL expert. Your task is to convert a natural language question into a valid SQLite3 SELECT query.
    We have multiple attached databases. Their schemas and aliases are below:
    
    {schema_info}
    
    Return ONLY the SQL query code. Do not include any explanation or markdown formatting like ```sql.
    
    CRITICAL RULES:
    - You must ONLY generate SELECT queries. Never generate DROP, DELETE, INSERT, UPDATE, ALTER, or any other modifying query.
    - Never include multiple statements or semicolons.
    - If the user's question is not related to data retrieval from the provided databases, return: SELECT 'Query not applicable' AS result
    - When querying a table, you MUST use the correct database alias prefix, e.g., db_0.table_name
    - Return relevant text content as the primary result.
    """
    
    prompt = f"Question: {user_query}"
    
    sql_query = generate_llm_response(system_prompt, prompt)
    sql_query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    
    return sql_query


def execute_sql(sql_query):
    if "Query not applicable" in sql_query:
        return []
        
    is_safe, reason = validate_sql(sql_query)
    if not is_safe:
        print(f"⚠️  SQL BLOCKED: {reason}")
        return []

    sql_files = get_sql_files()
    if not sql_files:
        return []

    try:
        # Create an empty in-memory DB and attach all uploaded databases in read-only mode
        conn = sqlite3.connect(":memory:")
        for i, file in enumerate(sql_files):
            file_path = os.path.join(UPLOAD_DIR, file)
            safe_path = file_path.replace("'", "''")
            # Using read-only URI in attach
            conn.execute(f"ATTACH DATABASE 'file:{safe_path}?mode=ro' AS db_{i}")
            
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(" | ".join(map(str, row)))
            return results
        finally:
            conn.close()
    except Exception as e:
        print(f"SQL execution error: {e}")
        return []


def retrieve_sql(query):
    sql = generate_sql(query)
    print(f"Generated SQL: {sql}")
    results = execute_sql(sql)
    return results

if __name__ == "__main__":
    test_query = "What is the policy for leave?"
    print(f"Testing with query: {test_query}")
    print(retrieve_sql(test_query))
