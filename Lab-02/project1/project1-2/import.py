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

def import_books():
    create_table()  # Ensure the table exists before inserting data

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        with open("books.csv", "r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            for isbn, title, author, year in reader:
                cur.execute(
                    "INSERT INTO books (isbn, title, author, year) VALUES (%s, %s, %s, %s) ON CONFLICT (isbn) DO NOTHING",
                    (isbn, title, author, year)
                )

        conn.commit()
        cur.close()
        conn.close()
        print("Books imported successfully!")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    import_books()
