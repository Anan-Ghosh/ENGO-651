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
            # Access the values by index (tuple indexing)
            if user[2] == password:  # user[2] is the password in the tuple
                session["user_id"] = user[0]  # user[0] is the id
                session["username"] = user[1]  # user[1] is the username
                flash("Login successful!", "success")
                return redirect("/")
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

if __name__ == "__main__":
    create_tables()  
    app.run(debug=True)
