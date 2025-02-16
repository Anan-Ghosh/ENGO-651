import os
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
from sqlalchemy import create_engine, text  # Import text()
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Ensure DATABASE_URL is set
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
    """Ensures the users table exists before inserting data."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """))
    db.commit()
    print("Users table created (if it didn't exist).")

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
            # user[2] is the stored password (hashed or plaintext)
            if user[2] == password:  # Ensure this matches how passwords are stored
                session["user_id"] = user[0]  # Store user ID in session
                session["username"] = user[1]  # Store username in session
                flash(f"Welcome, {session['username']}!", "success")
                return redirect("/search")  # Redirect to search page after login
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
        return redirect("/login")  # Redirect to login if not logged in

    books = None
    if request.method == "POST":
        query = request.form.get("query")
        if not query:
            flash("Please enter a search term.", "warning")
            return render_template("search.html", books=None)

        # Perform case-insensitive search
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


@app.route("/book/<isbn>")
def book_details(isbn):
    """Display details of a selected book."""
    if "user_id" not in session:
        flash("You must be logged in to view book details.", "danger")
        return redirect("/login")

    book = db.execute(text("SELECT * FROM books WHERE isbn = :isbn"), {"isbn": isbn}).fetchone()

    if not book:
        flash("Book not found.", "warning")
        return redirect("/search")

    return render_template("book.html", book={
        "id": book[0],
        "isbn": book[1],
        "title": book[2],
        "author": book[3],
        "year": book[4]
    })



if __name__ == "__main__":
    create_tables()  
    app.run(debug=True)
