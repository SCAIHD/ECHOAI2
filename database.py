import sqlite3
import json
import os
import datetime
from pathlib import Path
import streamlit as st

# Create the database directory if it doesn't exist
DB_DIR = Path("./data")
DB_DIR.mkdir(exist_ok=True)

# Database path
DB_PATH = DB_DIR / "transcription_history.db"

def init_db():
    """Initialize the database with necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table for users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create table for transcription history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_size REAL NOT NULL,
        file_type TEXT,
        transcription_id TEXT,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        transcription_text TEXT,
        config TEXT,
        duration REAL,
        transcript_name TEXT,
        transcript_comments TEXT,
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create table for AI analyses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcription_id INTEGER,
        model TEXT,
        analysis_text TEXT,
        prompt_template TEXT,
        token_usage INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
    )
    ''')
    
    # Create table for prompt templates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompt_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        template_text TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Migrations - add columns if they don't exist
    migrate_database(conn, cursor)
    
    conn.commit()
    conn.close()

def migrate_database(conn, cursor):
    """Add any missing columns to existing tables"""
    # Check if transcript_name column exists in transcriptions table
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add transcript_name column if it doesn't exist
    if 'transcript_name' not in columns:
        print("Adding transcript_name column to transcriptions table")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN transcript_name TEXT")
    
    # Add transcript_comments column if it doesn't exist
    if 'transcript_comments' not in columns:
        print("Adding transcript_comments column to transcriptions table")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN transcript_comments TEXT")
    
    # Add user_id column if it doesn't exist
    if 'user_id' not in columns:
        print("Adding user_id column to transcriptions table")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN user_id TEXT REFERENCES users(id)")
    
    # Check if user_id column exists in prompt_templates table
    cursor.execute("PRAGMA table_info(prompt_templates)")
    template_columns = [column[1] for column in cursor.fetchall()]
    
    # Add user_id column to prompt_templates if it doesn't exist
    if 'user_id' not in template_columns:
        print("Adding user_id column to prompt_templates table")
        cursor.execute("ALTER TABLE prompt_templates ADD COLUMN user_id TEXT REFERENCES users(id)")
    
    conn.commit()

def save_user(user_id, username, name, email, password_hash):
    """
    Save a new user to the database.
    
    Args:
        user_id (str): Unique identifier for the user (UUID)
        username (str): Username for login
        name (str): Display name
        email (str): Email address
        password_hash (str): Hashed password
        
    Returns:
        bool: True if user was created successfully
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO users (id, username, name, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, username, name, email, password_hash, datetime.datetime.now()
        ))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    """
    Get a user by their username.
    
    Args:
        username (str): Username to search for
        
    Returns:
        dict: User data if found, None otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    
    row = cursor.fetchone()
    user = dict(row) if row else None
    
    conn.close()
    return user

def save_transcription(file_name, file_size, file_type, transcription_id, language, 
                     transcription_text, config_options, duration=None, transcript_name=None, 
                     transcript_comments=None, user_id=None):
    """
    Save transcription details to the database.
    
    Args:
        file_name (str): Name of the audio file
        file_size (float): Size of the file in MB
        file_type (str): Type of the audio file
        transcription_id (str): AssemblyAI transcription ID
        language (str): Language code used for transcription
        transcription_text (str): The transcribed text
        config_options (dict): Configuration options used for transcription
        duration (float, optional): Duration of the audio in seconds
        transcript_name (str, optional): User-provided name for the transcript
        transcript_comments (str, optional): User-provided comments about the transcript
        user_id (str, optional): ID of the user who created this transcription
        
    Returns:
        int: ID of the saved record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert config_options to JSON string
    config_json = json.dumps(config_options)
    
    # Get the current user_id from session state if not provided
    if user_id is None and hasattr(st, 'session_state') and 'user_id' in st.session_state:
        user_id = st.session_state.user_id
    
    cursor.execute('''
    INSERT INTO transcriptions 
    (file_name, file_size, file_type, transcription_id, language, 
     transcription_text, config, duration, created_at, transcript_name, transcript_comments, user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        file_name, file_size, file_type, transcription_id, language,
        transcription_text, config_json, duration, datetime.datetime.now(), transcript_name, transcript_comments, user_id
    ))
    
    # Get the ID of the inserted record
    transcription_db_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return transcription_db_id

def save_analysis(transcription_db_id, model, analysis_text, prompt_template, token_usage):
    """
    Save AI analysis details to the database.
    
    Args:
        transcription_db_id (int): Database ID of the associated transcription
        model (str): OpenAI model used for analysis
        analysis_text (str): The analysis text from AI
        prompt_template (str): The prompt template used
        token_usage (int): Number of tokens used
        
    Returns:
        int: ID of the saved analysis record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO analyses 
    (transcription_id, model, analysis_text, prompt_template, token_usage, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        transcription_db_id, model, analysis_text, prompt_template, token_usage, 
        datetime.datetime.now()
    ))
    
    # Get the ID of the inserted record
    analysis_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return analysis_id

def get_all_transcriptions(limit=100, user_id=None):
    """
    Get all transcriptions from the database.
    
    Args:
        limit (int): Limit the number of records returned
        user_id (str, optional): If provided, only return transcriptions for this user
        
    Returns:
        list: List of transcription dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if transcript_name and transcript_comments columns exist
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Construct the SELECT statement based on available columns
    select_columns = "id, file_name, file_size, file_type, transcription_id, language, created_at, substr(transcription_text, 1, 300) as preview_text"
    
    if 'transcript_name' in columns:
        select_columns += ", transcript_name"
    
    if 'transcript_comments' in columns:
        select_columns += ", transcript_comments"
    
    if 'user_id' in columns:
        select_columns += ", user_id"
    
    # Start building the query
    query = f"SELECT {select_columns} FROM transcriptions"
    
    # Add user filtering if requested
    params = []
    if user_id is not None and 'user_id' in columns:
        query += " WHERE user_id = ?"
        params.append(user_id)
    
    # Add ordering and limit
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    transcriptions = [dict(row) for row in rows]
    
    conn.close()
    return transcriptions

def get_transcription(transcription_id):
    """
    Get a specific transcription by ID.
    
    Args:
        transcription_id (int): ID of the transcription to retrieve
        
    Returns:
        dict: Transcription data including full text
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Debug: Print transcription ID being requested
    print(f"DEBUG: Fetching transcription with ID: {transcription_id}")
    
    # Check if transcript_name and transcript_comments columns exist
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Construct the SELECT statement based on available columns
    select_columns = "id, file_name, file_size, file_type, transcription_id, language, created_at, transcription_text, config, duration"
    
    if 'transcript_name' in columns:
        select_columns += ", transcript_name"
    
    if 'transcript_comments' in columns:
        select_columns += ", transcript_comments"
    
    query = f"""
    SELECT {select_columns}
    FROM transcriptions
    WHERE id = ?
    """
    
    cursor.execute(query, (transcription_id,))
    
    row = cursor.fetchone()
    
    if row:
        transcription = dict(row)
        
        # Debug: Check what we got from the database
        print(f"DEBUG: Found transcription in DB. Has 'transcription_text': {'transcription_text' in transcription}")
        if 'transcription_text' in transcription:
            print(f"DEBUG: Transcription text length: {len(transcription['transcription_text']) if transcription['transcription_text'] else 0}")
        
        # Parse config JSON
        if transcription['config']:
            try:
                transcription['config'] = json.loads(transcription['config'])
            except:
                pass
        
        conn.close()
        return transcription
    else:
        print(f"DEBUG: No transcription found with ID: {transcription_id}")
    
    conn.close()
    return None

def get_analyses_for_transcription(transcription_id):
    """
    Retrieve all analyses for a specific transcription.
    
    Args:
        transcription_id (int): Database ID of the transcription
        
    Returns:
        list: List of analysis records
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM analyses 
    WHERE transcription_id = ?
    ORDER BY created_at DESC
    ''', (transcription_id,))
    
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return results

def delete_transcription(transcription_id):
    """
    Delete a transcription and its associated analyses.
    
    Args:
        transcription_id (int): Database ID of the transcription
        
    Returns:
        bool: True if successful
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First delete associated analyses (due to foreign key constraint)
    cursor.execute('''
    DELETE FROM analyses WHERE transcription_id = ?
    ''', (transcription_id,))
    
    # Then delete the transcription
    cursor.execute('''
    DELETE FROM transcriptions WHERE id = ?
    ''', (transcription_id,))
    
    conn.commit()
    conn.close()
    
    return True

def get_analysis(analysis_id):
    """
    Retrieve a specific analysis by ID.
    
    Args:
        analysis_id (int): Database ID of the analysis
        
    Returns:
        dict: Analysis record
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM analyses WHERE id = ?
    ''', (analysis_id,))
    
    row = cursor.fetchone()
    result = dict(row) if row else None
    
    conn.close()
    
    return result

# Add prompt template functions
def save_prompt_template(name, template_text, description=None, user_id=None):
    """
    Save a new prompt template to the database.
    
    Args:
        name (str): Name of the template
        template_text (str): Template text with {transcript} placeholder
        description (str, optional): Description of the template
        user_id (str, optional): ID of the user who created this template
        
    Returns:
        int: ID of the saved template
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the current user_id from session state if not provided
    if user_id is None and hasattr(st, 'session_state') and 'user_id' in st.session_state:
        user_id = st.session_state.user_id
    
    cursor.execute('''
    INSERT INTO prompt_templates (name, template_text, description, created_at, user_id)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        name, template_text, description, datetime.datetime.now(), user_id
    ))
    
    # Get the ID of the inserted record
    template_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return template_id

def get_prompt_templates(user_id=None):
    """
    Get all prompt templates from the database.
    
    Args:
        user_id (str, optional): If provided, only return templates for this user
        
    Returns:
        list: List of template dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Start building the query
    query = "SELECT * FROM prompt_templates"
    
    # Add user filtering if requested
    params = []
    cursor.execute("PRAGMA table_info(prompt_templates)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if user_id is not None and 'user_id' in columns:
        query += " WHERE user_id = ? OR user_id IS NULL"  # Include system templates
        params.append(user_id)
    
    # Add ordering
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    
    rows = cursor.fetchall()
    templates = [dict(row) for row in rows]
    
    conn.close()
    return templates

def get_prompt_template(template_id):
    """
    Retrieve a specific prompt template by ID.
    
    Args:
        template_id (int): Database ID of the template
        
    Returns:
        dict: Prompt template record
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM prompt_templates WHERE id = ?
    ''', (template_id,))
    
    row = cursor.fetchone()
    result = dict(row) if row else None
    
    conn.close()
    
    return result

def update_prompt_template(template_id, name, template_text, description=None):
    """
    Update an existing prompt template.
    
    Args:
        template_id (int): Database ID of the template
        name (str): Name of the template
        template_text (str): The prompt template text
        description (str, optional): Description of the template
        
    Returns:
        bool: True if successful
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE prompt_templates 
    SET name = ?, template_text = ?, description = ?
    WHERE id = ?
    ''', (name, template_text, description, template_id))
    
    conn.commit()
    conn.close()
    
    return True

def delete_prompt_template(template_id):
    """
    Delete a prompt template.
    
    Args:
        template_id (int): Database ID of the template
        
    Returns:
        bool: True if successful
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    DELETE FROM prompt_templates WHERE id = ?
    ''', (template_id,))
    
    conn.commit()
    conn.close()
    
    return True

# Initialize the database when this module is imported
init_db() 