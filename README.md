# Flask Bookstore App
A simple Flask web application for a bookstore with user registration, login, book browsing, search, cart, and admin features to add books and manage admin accounts.

# Description
This project is a Flask-based web application designed to simulate an online bookstore. It allows users to browse and search for books, add them to a cart, and manage their accounts. Admins have additional privileges to add new books and create new admin accounts. The application uses SQLite for data storage and implements secure password hashing for user authentication.
The app is structured to be user-friendly, with a login-first approach to ensure secure access to features. It includes debugging logs to help developers troubleshoot issues and is suitable for learning Flask, SQLite, and web development concepts.
# Installation
To set up the Flask Bookstore App on your local machine, follow these steps:

Clone the Repository:Clone the repository from GitHub:
git clone https://github.com/yourusername/flask-bookstore.git

Navigate to the Project Directory:Move into the project folder:
cd flask-bookstore

Install Dependencies:Install the required Python packages using the provided requirements.txt file:
pip install -r requirements.txt

Ensure you have Python 3 installed. The requirements.txt file includes:
Flask

# Running the App

Start the Application:Run the main Python script to start the Flask server:
python app.py

The app will automatically create a SQLite database (bookstore.db) in the project directory if it doesn't already exist.

Access the App:Open a web browser and navigate to http://localhost:5000. You will be redirected to the login page due to the login-first requirement.

Log In:Use the default admin credentials for testing:

Username: admin
Password: admin123
Alternatively, you can register a new user account via the /register route.

# Explore the App:

Browse and search for books.
Add books to your cart.
If logged in as an admin, add new books or create new admin accounts.

# Project Structure
The project is organized as follows:

File/Folder
Description

app.py
Main Flask application file with all routes and logic.

bookstore.db
SQLite database file storing books, users, admins, and cart data.

templates/
Folder containing HTML templates for the app.

templates/index.html
Home page to browse books.

templates/register.html
User registration page.

templates/login.html
User login page.

templates/cart.html
View cart page.

templates/add_book.html
Admin page to add new books.

templates/create_admin.html
Admin page to create new admin accounts.

requirements.txt
File listing Python dependencies (Flask).

Dependencies
The project requires the following Python packages:

Package
Description

Flask
Web framework for building the application.

Werkzeug
Used for password hashing (included with Flask).


Install dependencies using:
pip install -r requirements.txt

The requirements.txt file should contain:
Flask

The app also uses standard Python libraries (sqlite3, secrets, os, logging), which do not require separate installation.
Features

User Registration and Login: Users can create accounts and log in securely with hashed passwords.
Book Browsing and Search: Browse all books or search by title, author, or genre.
Shopping Cart: Add books to a cart for potential purchase.
Admin Features:
Add new books to the store via /admin/add.
Create new admin accounts via /admin/create (admin-only).

# Security:
Passwords are hashed using Werkzeug's generate_password_hash.
Admin keys are generated securely using secrets.token_hex and shown only to admins.

Debugging: Extensive logging is implemented to help troubleshoot issues.

Creating Admin Accounts
The app initializes with a default admin account:

Username: admin
Password: admin123

To create additional admin accounts:

Log in as an existing admin.
Navigate to /admin/create.
Enter a new username and password in the form.
Upon successful creation, the new admin key will be displayed in a flash message (visible only to admins).

# Contact
For questions, feedback, or collaboration opportunities, reach out on X: @Emitsunechika.
