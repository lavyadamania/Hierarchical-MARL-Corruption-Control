import sqlite3
import os
from contextlib import contextmanager

class DBManager:
    def __init__(self, db_path, schema_path):
        self.db_path = db_path
        self.schema_path = schema_path
        self.initialize_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def initialize_db(self):
        """Creates the database and tables if they don't exist."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.get_connection() as conn:
            with open(self.schema_path, 'r') as f:
                schema_script = f.read()
            conn.executescript(schema_script)
            conn.commit()

    def execute_query(self, query, params=()):
        """Executes a query and commits. Returns cursor for selection."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    def fetch_one(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def close(self):
        # SQLite connections in context managers close automatically, but explicit method provided if needed
        pass

    def update_cop_status(self, cop_id, status):
        """Updates the status of a cop (e.g. active, killed, fired)."""
        self.execute_query("UPDATE cops SET status=? WHERE cop_id=?", (status, cop_id))

    def log_transaction(self, episode, cop_id, crime_type, offer, decision, outcome):
        """Logs a bribe transaction to history."""
        # Note: crime_type is not currently stored in schema, but passed for potential future use
        self.execute_query("""
            INSERT INTO bribe_history (episode_number, cop_id, player_offer, decision, outcome)
            VALUES (?, ?, ?, ?, ?)
        """, (episode, cop_id, offer, decision, outcome))
