Book Review Website
This web application allows users to search for books, view detailed book information, and submit reviews. Key features include:

User Authentication: Users can register, log in, and log out.
Book Search: Search books by ISBN, title, or author.
Book Details: Each book page displays title, author, publication year, ISBN, and both local reviews and external information.
Review Submission: Logged-in users can submit a single review per book, including a rating (1–5) and an optional comment.
External API Integration:
Google Books API: Retrieves additional book details (e.g., average rating, ratings count, published date, and description).
Google Gemini API: Summarizes the book description to under 50 words.
API Endpoint: Access book details programmatically via /api/<isbn>, which returns a JSON response with all relevant book and review data.