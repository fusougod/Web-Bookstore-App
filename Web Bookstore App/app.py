import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')  # Explicitly set template folder
app.secret_key = secrets.token_hex(16)  # Generate a random secret key for the app
logger.debug("Flask app initialized")

# Database setup
def init_db():
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookstore.db')
        logger.debug(f"Attempting to create database at {db_path}")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        logger.debug("Database connected successfully")
        c.execute('''CREATE TABLE IF NOT EXISTS books
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      author TEXT NOT NULL,
                      genre TEXT,
                      price REAL NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL UNIQUE,
                      password TEXT NOT NULL,
                      user_key TEXT NOT NULL UNIQUE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL UNIQUE,
                      password TEXT NOT NULL,
                      admin_key TEXT NOT NULL UNIQUE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS cart
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      book_id INTEGER,
                      quantity INTEGER,
                      FOREIGN KEY(user_id) REFERENCES users(id),
                      FOREIGN KEY(book_id) REFERENCES books(id))''')
        # Sample data for books
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 10.99),
            ('Python Crash Course', 'Eric Matthes', 'Education', 29.99),
            ('Dune', 'Frank Herbert', 'Sci-Fi', 15.99)
        ]
        c.executemany('INSERT OR IGNORE INTO books (title, author, genre, price) VALUES (?, ?, ?, ?)', sample_books)
        # Sample admin with unique key
        admin_key = secrets.token_hex(16)
        c.execute('INSERT OR IGNORE INTO admins (username, password, admin_key) VALUES (?, ?, ?)',
                  ('admin', generate_password_hash('admin123'), admin_key))
        # Your personal admin account
        your_admin_key = secrets.token_hex(16)
        c.execute('INSERT OR IGNORE INTO admins (username, password, admin_key) VALUES (?, ?, ?)',
                  ('your_username', generate_password_hash('your_secure_password'), your_admin_key))
        conn.commit()
        conn.close()
        logger.debug(f"Database created and populated at {db_path}")
        return db_path
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Connect to database
def get_db():
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookstore.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logger.debug("Database connection opened")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

# Check login status for protected routes
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            logger.debug("User not logged in, redirecting to login")
            flash('Please log in to access this page!', 'error')
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

# Home page - Browse books
@app.route('/')
@login_required
def index():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM books')
        books = c.fetchall()
        conn.close()
        logger.debug("Rendering index.html with books")
        return render_template('index.html', books=books)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash('An error occurred while loading books!', 'error')
        return redirect(url_for('login'))

# Search books
@app.route('/search')
@login_required
def search():
    try:
        query = request.args.get('query', '')
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?',
                  (f'%{query}%', f'%{query}%', f'%{query}%'))
        books = c.fetchall()
        conn.close()
        logger.debug(f"Rendering index.html for search with query: {query}")
        return render_template('index.html', books=books, query=query)
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        flash('An error occurred while searching!', 'error')
        return redirect(url_for('index'))

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                logger.debug("Missing username or password in registration")
                flash('Username and password are required!', 'error')
                return render_template('register.html')
            user_key = secrets.token_hex(16)
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password, user_key) VALUES (?, ?, ?)',
                      (username, generate_password_hash(password), user_key))
            conn.commit()
            conn.close()
            logger.debug(f"User {username} registered successfully")
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        logger.debug("Rendering register.html")
        return render_template('register.html')
    except sqlite3.IntegrityError:
        logger.error(f"Username {username} already exists")
        flash('Username already exists!', 'error')
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error in register route: {e}")
        flash('An error occurred during registration!', 'error')
        return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                logger.debug("Missing username or password in login")
                flash('Username and password are required!', 'error')
                return render_template('login.html')
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()
            if not user:
                c.execute('SELECT * FROM admins WHERE username = ?', (username,))
                admin = c.fetchone()
                if admin and check_password_hash(admin['password'], password):
                    session['user_id'] = admin['id']
                    session['username'] = admin['username']
                    session['is_admin'] = True
                    admin_key = admin["admin_key"]
                    conn.close()
                    logger.debug(f"Admin {username} logged in")
                    flash(f'Logged in successfully! Admin key: {admin_key}', 'success')
                    return redirect(url_for('index'))
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = False
                conn.close()
                logger.debug(f"User {username} logged in")
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            conn.close()
            logger.debug(f"Failed login attempt for {username}")
            flash('Invalid username or password!', 'error')
        logger.debug("Rendering login.html")
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {e}")
        flash('An error occurred during login!', 'error')
        return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    try:
        session.clear()
        logger.debug("User logged out")
        flash('Logged out successfully!', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in logout route: {e}")
        flash('An error occurred during logout!', 'error')
        return redirect(url_for('login'))

# Add to cart
@app.route('/add_to_cart/<int:book_id>')
@login_required
def add_to_cart(book_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM books WHERE id = ?', (book_id,))
        book = c.fetchone()
        if not book:
            conn.close()
            logger.debug(f"Book ID {book_id} not found")
            flash('Book not found!', 'error')
            return redirect(url_for('index'))
        c.execute('SELECT * FROM cart WHERE user_id = ? AND book_id = ?', (session['user_id'], book_id))
        existing = c.fetchone()
        if existing:
            c.execute('UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND book_id = ?',
                      (session['user_id'], book_id))
        else:
            c.execute('INSERT INTO cart (user_id, book_id, quantity) VALUES (?, ?, 1)',
                      (session['user_id'], book_id))
        conn.commit()
        conn.close()
        logger.debug(f"Book ID {book_id} added to cart for user {session['user_id']}")
        flash('Book added to cart!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in add_to_cart route: {e}")
        flash('An error occurred while adding to cart!', 'error')
        return redirect(url_for('index'))

# View cart
@app.route('/cart')
@login_required
def cart():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT b.*, c.quantity
                     FROM cart c
                     JOIN books b ON c.book_id = b.id
                     WHERE c.user_id = ?''', (session['user_id'],))
        cart_items = c.fetchall()
        total = sum(item['price'] * item['quantity'] for item in cart_items)
        conn.close()
        logger.debug(f"Rendering cart.html for user {session['user_id']}")
        return render_template('cart.html', cart_items=cart_items, total=total)
    except Exception as e:
        logger.error(f"Error in cart route: {e}")
        flash('An error occurred while loading cart!', 'error')
        return redirect(url_for('index'))

# Admin: Add book
@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_book():
    try:
        if not session.get('is_admin', False):
            logger.debug("Non-admin attempted to access add_book")
            flash('Access denied! Admin only.', 'error')
            return redirect(url_for('index'))
        if request.method == 'POST':
            title = request.form.get('title')
            author = request.form.get('author')
            genre = request.form.get('genre')
            price = request.form.get('price')
            if not title or not author or not price:
                logger.debug("Missing title, author, or price in add_book")
                flash('Title, author, and price are required!', 'error')
                return render_template('add_book.html')
            try:
                price = float(price)
            except ValueError:
                logger.debug("Invalid price format in add_book")
                flash('Price must be a valid number!', 'error')
                return render_template('add_book.html')
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO books (title, author, genre, price) VALUES (?, ?, ?, ?)',
                      (title, author, genre, price))
            conn.commit()
            conn.close()
            logger.debug(f"Book '{title}' added by admin {session['username']}")
            flash('Book added successfully!', 'success')
            return redirect(url_for('index'))
        logger.debug("Rendering add_book.html")
        return render_template('add_book.html')
    except Exception as e:
        logger.error(f"Error in add_book route: {e}")
        flash('An error occurred while adding book!', 'error')
        return redirect(url_for('index'))

# Admin: Create new admin account
@app.route('/admin/create', methods=['GET', 'POST'])
@login_required
def create_admin():
    try:
        if not session.get('is_admin', False):
            logger.debug("Non-admin attempted to access create_admin")
            flash('Access denied! Admin only.', 'error')
            return redirect(url_for('index'))
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                logger.debug("Missing username or password in create_admin")
                flash('Username and password are required!', 'error')
                return render_template('create_admin.html')
            admin_key = secrets.token_hex(16)
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO admins (username, password, admin_key) VALUES (?, ?, ?)',
                      (username, generate_password_hash(password), admin_key))
            conn.commit()
            conn.close()
            logger.debug(f"New admin {username} created by {session['username']}")
            flash(f'Admin account created successfully! Admin key: {admin_key}', 'success')
            return redirect(url_for('index'))
        logger.debug("Rendering create_admin.html")
        return render_template('create_admin.html')
    except sqlite3.IntegrityError:
        logger.error(f"Username {username} already exists for admin creation")
        flash('Username already exists!', 'error')
        return render_template('create_admin.html')
    except Exception as e:
        logger.error(f"Error in create_admin route: {e}")
        flash('An error occurred while creating admin account!', 'error')
        return render_template('create_admin.html')

# Initialize database and run the app
if __name__ == '__main__':
    try:
        db_path = init_db()
        if not os.path.exists(db_path):
            logger.error("Database file was not created!")
        else:
            logger.debug("Database initialized successfully!")
        logger.debug("Starting Flask server on http://127.0.0.1:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting the app: {e}")