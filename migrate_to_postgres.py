import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Load environment variables if any
load_dotenv()

# Database connection details
SQLITE_DB_PATH = 'kgen_gaming_support_advanced.db'
POSTGRES_CONNECTION_STRING = 'postgresql://kgen_support_user:RvrBwQGoteFm8Hozya4E7PzN3wR8LPGv@dpg-d0boqtbuibrs73dhp990-a.singapore-postgres.render.com/kgen_support'

def get_sqlite_tables():
    """Get all tables from SQLite database"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    table_list = [table[0] for table in tables if table[0] != 'sqlite_sequence']
    
    print(f"Found tables in SQLite: {table_list}")
    
    return table_list

def get_table_schema(table_name):
    """Get the schema for a specific table"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name});")
    schema = cursor.fetchall()
    
    columns = []
    for col in schema:
        col_id, col_name, col_type, not_null, default_val, pk = col
        columns.append({
            'name': col_name,
            'type': convert_type(col_type),
            'not_null': not_null == 1,
            'is_pk': pk == 1
        })
    
    return columns

def convert_type(sqlite_type):
    """Convert SQLite types to PostgreSQL types"""
    sqlite_type = sqlite_type.upper()
    
    if 'INT' in sqlite_type:
        return 'INTEGER'
    elif 'CHAR' in sqlite_type or 'TEXT' in sqlite_type or 'CLOB' in sqlite_type:
        return 'TEXT'
    elif 'BLOB' in sqlite_type:
        return 'BYTEA'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'NUMERIC'
    else:
        return 'TEXT'  # Default to TEXT for unknown types

def create_postgres_table(table_name, columns):
    """Create a table in PostgreSQL"""
    conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
    cursor = conn.cursor()
    
    # Build CREATE TABLE statement
    column_defs = []
    primary_keys = []
    
    for col in columns:
        col_def = f"{col['name']} {col['type']}"
        
        if col['not_null']:
            col_def += " NOT NULL"
            
        if col['is_pk']:
            primary_keys.append(col['name'])
            
        column_defs.append(col_def)
    
    if primary_keys:
        column_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
    
    create_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)});"
    
    print(f"Creating table {table_name} in PostgreSQL...")
    print(create_statement)
    
    try:
        cursor.execute(create_statement)
        conn.commit()
        print(f"Table {table_name} created successfully!")
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()

def transfer_data(table_name):
    """Transfer data from SQLite to PostgreSQL"""
    # Get data from SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlite_cursor.execute(f"SELECT * FROM {table_name};")
    rows = sqlite_cursor.fetchall()
    
    # Get column names
    sqlite_cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    sqlite_cursor.close()
    sqlite_conn.close()
    
    if not rows:
        print(f"No data found in table {table_name}")
        return
    
    # Insert data into PostgreSQL
    pg_conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
    pg_cursor = pg_conn.cursor()
    
    # Build INSERT statement with placeholders
    placeholders = ','.join(['%s'] * len(columns))
    insert_statement = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders});"
    
    print(f"Transferring {len(rows)} rows to {table_name}...")
    
    try:
        pg_cursor.executemany(insert_statement, rows)
        pg_conn.commit()
        print(f"Successfully transferred {len(rows)} rows to {table_name}")
    except Exception as e:
        print(f"Error transferring data to {table_name}: {e}")
        pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()

def main():
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"SQLite database file not found: {SQLITE_DB_PATH}")
        sys.exit(1)
    
    print("Starting migration from SQLite to PostgreSQL...")
    print(f"Source: {SQLITE_DB_PATH}")
    print(f"Destination: PostgreSQL database")
    
    try:
        # Test PostgreSQL connection
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        conn.close()
        print("Successfully connected to PostgreSQL")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    
    # Get all tables
    tables = get_sqlite_tables()
    
    # Process each table
    for table in tables:
        # Get table schema
        columns = get_table_schema(table)
        
        # Create table in PostgreSQL
        create_postgres_table(table, columns)
        
        # Transfer data
        transfer_data(table)
    
    print("Migration completed!")

if __name__ == "__main__":
    main() 