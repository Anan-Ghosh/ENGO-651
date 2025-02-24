import os
import requests
from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Ensure required environment variables are set
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database connection
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def create_tables():
    """Create necessary tables if they do not exist."""
    # Create users table
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """))
    # Create reviews table with a unique constraint to prevent duplicate reviews per user/book
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            book_id INTEGER REFERENCES books(id),
            rating INTEGER NOT NULL,
            review_text TEXT,
            UNIQUE (user_id, book_id)
        )
    """))
    db.commit()
    print("Users and Reviews tables created (if they didn't exist).")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Insert user into the database
        try:
            db.execute(text("INSERT INTO users (username, password) VALUES (:username, :password)"),
                       {"username": username, "password": password})
            db.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect("/login")
        except Exception:
            flash("Username already taken. Try another one.", "danger")
            return redirect("/register")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Fetch user from the database
        user = db.execute(text("SELECT * FROM users WHERE username = :username"), {"username": username}).fetchone()

        if user:
            if user[2] == password:  # Ensure this matches how passwords are stored
                session["user_id"] = user[0]
                session["username"] = user[1]
                flash(f"Welcome, {session['username']}!", "success")
                return redirect("/search")
            else:
                flash("Invalid password", "danger")
        else:
            flash("Invalid username", "danger")

        return redirect("/login")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Allows logged-in users to search for books."""
    if "user_id" not in session:
        flash("You must be logged in to access this page.", "danger")
        return redirect("/login")

    books = None
    if request.method == "POST":
        query = request.form.get("query")
        if not query:
            flash("Please enter a search term.", "warning")
            return render_template("search.html", books=None)

        books = db.execute(text("""
            SELECT * FROM books
            WHERE 
                LOWER(isbn) LIKE LOWER(:query) OR
                LOWER(title) LIKE LOWER(:query) OR
                LOWER(author) LIKE LOWER(:query)
        """), {"query": f"%{query}%"}).fetchall()

        if not books:
            flash("No books found. Try a different search term.", "warning")

    return render_template("search.html", books=books)

@app.route("/book/<isbn>", methods=["GET", "POST"])
def book_details(isbn):
    """Display details of a selected book and handle review submissions."""
    if "user_id" not in session:
        flash("You must be logged in to view book details.", "danger")
        return redirect("/login")

    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()
    if not book:
        flash("Book not found.", "warning")
        return redirect("/search")

    book_id = book[0]

    # Handle review submission (POST)
    if request.method == "POST":
        rating = request.form.get("rating")
        review_text = request.form.get("review_text")

        # Check for duplicate review
        existing_review = db.execute(text(
            "SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id"
        ), {"user_id": session["user_id"], "book_id": book_id}).fetchone()

        if existing_review:
            flash("You have already submitted a review for this book.", "warning")
            return redirect(f"/book/{isbn}")

        db.execute(text("""
            INSERT INTO reviews (user_id, book_id, rating, review_text)
            VALUES (:user_id, :book_id, :rating, :review_text)
        """), {"user_id": session["user_id"], "book_id": book_id, "rating": rating, "review_text": review_text})
        db.commit()
        flash("Review submitted successfully.", "success")
        return redirect(f"/book/{isbn}")

    # For GET: Retrieve local reviews
    reviews = db.execute(text("SELECT rating, review_text FROM reviews WHERE book_id = :book_id"),
                         {"book_id": book_id}).fetchall()

    # Call Google Books API to get external details
    google_avg_rating = None
    google_ratings_count = None
    google_description = None
    google_publishedDate = None
    isbn10 = None
    isbn13 = None

    google_response = requests.get("https://www.googleapis.com/books/v1/volumes", 
                                   params={"q": f"isbn:{isbn}"})
    google_data = google_response.json()
    if "items" in google_data:
        volumeInfo = google_data["items"][0].get("volumeInfo", {})
        google_avg_rating = volumeInfo.get("averageRating")
        google_ratings_count = volumeInfo.get("ratingsCount")
        google_description = volumeInfo.get("description")
        google_publishedDate = volumeInfo.get("publishedDate")
        for ident in volumeInfo.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_10":
                isbn10 = ident.get("identifier")
            if ident.get("type") == "ISBN_13":
                isbn13 = ident.get("identifier")

    # Call Gemini API to summarize the description
    summarized_description = None
    if google_description:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            gemini_response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                params={"key": gemini_api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": "summarize this text using less than 50 words: " + google_description
                        }]
                    }]
                }
            )
            gemini_data = gemini_response.json()
            try:
                summarized_description = gemini_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                summarized_description = None

    return render_template("book.html", 
                           book={
                               "id": book[0],
                               "isbn": book[1],
                               "title": book[2],
                               "author": book[3],
                               "year": book[4]
                           },
                           reviews=reviews,
                           google_avg_rating=google_avg_rating,
                           google_ratings_count=google_ratings_count,
                           google_publishedDate=google_publishedDate,
                           isbn10=isbn10,
                           isbn13=isbn13,
                           summarized_description=summarized_description)

@app.route("/api/<isbn>")
def api_book(isbn):
    """Return a JSON response with details about the book."""
    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    # Get external book data from Google Books API
    google_publishedDate = None
    google_description = None
    isbn10 = None
    isbn13 = None
    google_response = requests.get("https://www.googleapis.com/books/v1/volumes",
                                   params={"q": f"isbn:{isbn}"})
    google_data = google_response.json()
    if "items" in google_data:
        volumeInfo = google_data["items"][0].get("volumeInfo", {})
        google_publishedDate = volumeInfo.get("publishedDate")
        google_description = volumeInfo.get("description")
        for ident in volumeInfo.get("industryIdentifiers", []):
            if ident.get("type") == "ISBN_10":
                isbn10 = ident.get("identifier")
            if ident.get("type") == "ISBN_13":
                isbn13 = ident.get("identifier")

    # Calculate local review statistics
    reviews = db.execute(text("SELECT rating FROM reviews WHERE book_id = :book_id"),
                         {"book_id": book[0]}).fetchall()
    review_count = len(reviews)
    if review_count > 0:
        average_rating = round(sum([r[0] for r in reviews]) / review_count, 2)
    else:
        average_rating = None

    # Get summarized description via Gemini API
    summarized_description = None
    if google_description:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            gemini_response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                params={"key": gemini_api_key},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{
                            "text": "summarize this text using less than 50 words: " + google_description
                        }]
                    }]
                }
            )
            gemini_data = gemini_response.json()
            try:
                summarized_description = gemini_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                summarized_description = None

    response = {
        "title": book[2] if book[2] else None,
        "author": book[3] if book[3] else None,
        "publishedDate": google_publishedDate if google_publishedDate else None,
        "ISBN_10": isbn10 if isbn10 else None,
        "ISBN_13": isbn13 if isbn13 else None,
        "reviewCount": review_count,
        "averageRating": average_rating,
        "description": google_description if google_description else None,
        "summarizedDescription": summarized_description if summarized_description else None
    }
    return jsonify(response)

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
