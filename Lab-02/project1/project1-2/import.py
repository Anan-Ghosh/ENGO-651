import os
import csv
from sqlalchemy import create_engine, text  
from sqlalchemy.orm import scoped_session, sessionmaker

# Ensure DATABASE_URL is set
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database connection
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def create_books_table():
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            isbn VARCHAR(20) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    """))
    db.commit()
    print("Books table created (if it didn't exist).")

def import_books():
    """Reads books.csv and inserts data into the books table, avoiding duplicates."""
    create_books_table()  

    with open("books.csv", "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for row in reader:
            if len(row) != 4:
                print(f"Skipping invalid row: {row}")  # Debugging invalid rows
                continue  

            isbn, title, author, year = [col.strip() for col in row]  # Trim spaces

            # Check if the book is already in the database
            existing_book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()
            if existing_book:
                print(f"Skipping duplicate book: {isbn} - {title}")
                continue  # Skip inserting duplicates

            try:
                db.execute(text(
                    "INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"),
                    {"isbn": isbn, "title": title, "author": author, "year": int(year)}
                )
            except Exception as e:
                print(f"Error inserting row {row}: {e}")  

    db.commit()
    print("Books imported successfully!")

if __name__ == "__main__":
    import_books()
