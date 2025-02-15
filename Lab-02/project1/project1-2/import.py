import csv
import psycopg2

# Database connection settings
DB_NAME = "Book"
DB_USER = "postgres"
DB_PASSWORD = "vagabond241998"
DB_HOST = "localhost"
DB_PORT = "5432"

def create_table():
    conn = psycopg2.connect(               ##Creates the books table if it does not exist.
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            isbn VARCHAR(20) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Table created successfully!")

