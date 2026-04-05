"""
SQLite audit trail. Every agent interaction is logged.
Allows full replay and debugging of extraction decisions.
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "audit.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS extraction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        source_file TEXT NOT NULL,
        extraction_method TEXT,
        doc_types_detected TEXT,
        tool_called TEXT,
        tool_input TEXT,
        raw_response TEXT,
        status TEXT DEFAULT 'success',
        error_message TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS run_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_timestamp TEXT,
        total_files INTEGER,
        successful INTEGER,
        failed INTEGER,
        output_file TEXT)
        """)
        conn.commit()

def log_extraction(
    source_file:str,
    extraction_method: str,
    doc_types: list,
    tool_called: str,
    tool_input: dict,
    raw_response: dict,
    status: str = "success",
    error_message: str = None
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO extraction_logs 
            (
            timestamp, source_file, extraction_method, doc_types_detected, tool_called, tool_input, raw_response, status, error_message)
            VALUES (?,?,?,?,?,?,?,?,?)            
            """, (
                datetime.now(timezone.utc).isoformat(),
                source_file,
                extraction_method,
                json.dumps(doc_types),
                tool_called,
                json.dumps(tool_input),
                json.dumps(raw_response),
                status,
                error_message
            )
        )
        conn.commit()

def log_run_summary(total: int, successful: int, failed: int, output_file: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO run_summary 
            (run_timestamp, total_files, successful, failed, output_file)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            total, successful, failed, output_file
        ))
        conn.commit()

# Ensure DB is initialized when module is imported
init_db()