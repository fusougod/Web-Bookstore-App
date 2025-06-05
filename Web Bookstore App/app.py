import logging
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = secrets.token_hex(16)
logger.debug("Flask app initialized")

# MySQL configurations for XAMPP
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Default XAMPP MySQL password is empty
app.config['MYSQL_DB'] = 'bookstore'
mysql = MySQL(app)

# Initialize the database and create default admin
def init_db():
    try:
        logger.debug("Attempting to initialize database")
        cursor = mysql.connection.cursor()

        # Drop existing tables to ensure a clean database
        cursor.execute('DROP TABLE IF EXISTS wishlist')
        cursor.execute('DROP TABLE IF EXISTS cart')
        cursor.execute('DROP TABLE IF EXISTS books')
        cursor.execute('DROP TABLE IF EXISTS admins')
        cursor.execute('DROP TABLE IF EXISTS users')

        # Create tables
        cursor.execute('''CREATE TABLE users
                          (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                           username VARCHAR(50) NOT NULL UNIQUE,
                           password VARCHAR(255) NOT NULL,
                           user_key VARCHAR(50) NOT NULL UNIQUE)''')
        cursor.execute('''CREATE TABLE admins
                          (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                           username VARCHAR(50) NOT NULL UNIQUE,
                           password VARCHAR(255) NOT NULL,
                           admin_key VARCHAR(50) NOT NULL UNIQUE)''')
        cursor.execute('''CREATE TABLE books
                          (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                           title VARCHAR(100) NOT NULL,
                           author VARCHAR(100) NOT NULL,
                           genre VARCHAR(50),
                           price DECIMAL(10, 2) NOT NULL)''')
        cursor.execute('''CREATE TABLE cart
                          (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                           user_id INTEGER,
                           book_id INTEGER,
                           quantity INTEGER,
                           FOREIGN KEY(user_id) REFERENCES users(id),
                           FOREIGN KEY(book_id) REFERENCES books(id))''')
        cursor.execute('''CREATE TABLE wishlist
                          (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                           user_id INTEGER,
                           book_id INTEGER,
                           FOREIGN KEY(user_id) REFERENCES users(id),
                           FOREIGN KEY(book_id) REFERENCES books(id))''')

        # Create default admin account
        admin_username = 'admin'
        admin_password = 'admin123password'
        admin_key = secrets.token_hex(8)
        hashed_password = generate_password_hash(admin_password)
        cursor.execute('INSERT INTO admins (username, password, admin_key) VALUES (%s, %s, %s)',
                       (admin_username, hashed_password, admin_key))

        mysql.connection.commit()
        logger.debug("Database tables created and default admin account added successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    finally:
        cursor.close()

# Call init_db to set up the database
with app.app_context():
    init_db()

# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    try:
        cursor = mysql.connection.cursor()
        # Default query to get all books
        query = 'SELECT * FROM books'
        params = []

        # Handle filters from the form
        genre = request.args.get('genre')
        price_range = request.args.get('price_range')

        if genre and genre != 'all':
            query += ' WHERE genre = %s'
            params.append(genre)
        if price_range:
            if price_range == '0-10':
                query += ' WHERE price BETWEEN %s AND %s' if not genre else ' AND price BETWEEN %s AND %s'
                params.extend([0, 10])
            elif price_range == '10-20':
                query += ' WHERE price BETWEEN %s AND %s' if not genre else ' AND price BETWEEN %s AND %s'
                params.extend([10, 20])
            elif price_range == '20+':
                query += ' WHERE price >= %s' if not genre else ' AND price >= %s'
                params.append(20)

        cursor.execute(query, params)
        books = cursor.fetchall()
        cursor.close()
        return render_template('index.html', books=books, genre=genre, price_range=price_range)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        flash('An error occurred while fetching books!', 'error')
        return render_template('index.html', books=[])

@app.route('/search')
def search():
    query = request.args.get('query', '')
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM books WHERE title LIKE %s OR author LIKE %s OR genre LIKE %s',
                       (f'%{query}%', f'%{query}%', f'%{query}%'))
        books = cursor.fetchall()
        cursor.close()
        return render_template('index.html', books=books, query=query)
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        flash('An error occurred while searching books!', 'error')
        return render_template('index.html', books=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_key = secrets.token_hex(8)
        hashed_password = generate_password_hash(password)
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO users (username, password, user_key) VALUES (%s, %s, %s)',
                           (username, hashed_password, user_key))
            mysql.connection.commit()
            cursor.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error in register route: {e}")
            flash('Username already exists!', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                session['username'] = username
                session['user_id'] = user[0]
                session['is_admin'] = False
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            cursor.execute('SELECT * FROM admins WHERE username = %s', (username,))
            admin = cursor.fetchone()
            if admin and check_password_hash(admin[2], password):
                session['username'] = username
                session['user_id'] = admin[0]
                session['is_admin'] = True
                flash('Logged in as admin successfully!', 'success')
                return redirect(url_for('index'))
            flash('Invalid username or password!', 'error')
            cursor.close()
        except Exception as e:
            logger.error(f"Error in login route: {e}")
            flash('An error occurred while logging in!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if not session.get('is_admin', False):
        flash('Access denied! Admin only.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        price = float(request.form['price'])
        try:
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO books (title, author, genre, price) VALUES (%s, %s, %s, %s)',
                           (title, author, genre, price))
            mysql.connection.commit()
            cursor.close()
            flash('Book added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error in add_book route: {e}")
            flash('An error occurred while adding book!', 'error')
    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    if not session.get('is_admin', False):
        flash('Access denied! Admin only.', 'error')
        return redirect(url_for('index'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM books WHERE id = %s', (book_id,))
        book = cursor.fetchone()
        if not book:
            flash('Book not found!', 'error')
            return redirect(url_for('index'))
        if request.method == 'POST':
            title = request.form['title']
            author = request.form['author']
            genre = request.form['genre']
            price = float(request.form['price'])
            cursor.execute('UPDATE books SET title = %s, author = %s, genre = %s, price = %s WHERE id = %s',
                           (title, author, genre, price, book_id))
            mysql.connection.commit()
            cursor.close()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('index'))
        cursor.close()
        return render_template('edit_book.html', book=book)
    except Exception as e:
        logger.error(f"Error in edit_book route: {e}")
        flash('An error occurred while editing book!', 'error')
        return redirect(url_for('index'))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    if not session.get('is_admin', False):
        flash('Access denied! Admin only.', 'error')
        return redirect(url_for('index'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM cart WHERE book_id = %s', (book_id,))
        cursor.execute('DELETE FROM wishlist WHERE book_id = %s', (book_id,))
        cursor.execute('DELETE FROM books WHERE id = %s', (book_id,))
        if cursor.rowcount == 0:
            flash('Book not found', 'error')
        else:
            flash('Book deleted successfully', 'success')
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error in delete_book route: {e}")
        flash('An error occurred while deleting book!', 'error')
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:book_id>')
def add_to_cart(book_id):
    if 'user_id' not in session:
        flash('Please login to add to cart!', 'error')
        return redirect(url_for('login'))
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM cart WHERE user_id = %s AND book_id = %s',
                       (session['user_id'], book_id))
        cart_item = cursor.fetchone()
        if cart_item:
            cursor.execute('UPDATE cart SET quantity = quantity + 1 WHERE id = %s', (cart_item[0],))
        else:
            cursor.execute('INSERT INTO cart (user_id, book_id, quantity) VALUES (%s, %s, 1)',
                           (session['user_id'], book_id))
        mysql.connection.commit()
        cursor.close()
        flash('Book added to cart!', 'success')
    except Exception as e:
        logger.error(f"Error in add_to_cart route: {e}")
        flash('An error occurred while adding to cart!', 'error')
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def cart():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT cart.id, books.title, books.price, cart.quantity
                          FROM cart JOIN books ON cart.book_id = books.id
                          WHERE cart.user_id = %s''', (session['user_id'],))
        cart_items = cursor.fetchall()
        cursor.close()
        return render_template('cart.html', cart_items=cart_items)
    except Exception as e:
        logger.error(f"Error in cart route: {e}")
        flash('An error occurred while fetching cart!', 'error')
        return render_template('cart.html', cart_items=[])

@app.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    quantity = int(request.form['quantity'])
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s',
                       (quantity, cart_id, session['user_id']))
        mysql.connection.commit()
        cursor.close()
        flash('Cart updated successfully!', 'success')
    except Exception as e:
        logger.error(f"Error in update_cart route: {e}")
        flash('An error occurred while updating cart!', 'error')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM cart WHERE id = %s AND user_id = %s',
                       (cart_id, session['user_id']))
        mysql.connection.commit()
        cursor.close()
        flash('Item removed from cart!', 'success')
    except Exception as e:
        logger.error(f"Error in remove_from_cart route: {e}")
        flash('An error occurred while removing from cart!', 'error')
    return redirect(url_for('cart'))

@app.route('/add_to_wishlist/<int:book_id>', methods=['POST'])
@login_required
def add_to_wishlist(book_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM wishlist WHERE user_id = %s AND book_id = %s',
                       (session['user_id'], book_id))
        if cursor.fetchone():
            flash('Book already in wishlist!', 'error')
        else:
            cursor.execute('INSERT INTO wishlist (user_id, book_id) VALUES (%s, %s)',
                           (session['user_id'], book_id))
            mysql.connection.commit()
            flash('Book added to wishlist!', 'success')
        cursor.close()
    except Exception as e:
        logger.error(f"Error in add_to_wishlist route: {e}")
        flash('An error occurred while adding to wishlist!', 'error')
    return redirect(url_for('index'))

@app.route('/wishlist')
@login_required
def wishlist():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT wishlist.id, books.title, books.author, books.genre, books.price
                          FROM wishlist JOIN books ON wishlist.book_id = books.id
                          WHERE wishlist.user_id = %s''', (session['user_id'],))
        wishlist_items = cursor.fetchall()
        cursor.close()
        return render_template('wishlist.html', wishlist_items=wishlist_items)
    except Exception as e:
        logger.error(f"Error in wishlist route: {e}")
        flash('An error occurred while fetching wishlist!', 'error')
        return render_template('wishlist.html', wishlist_items=[])

@app.route('/wishlist/remove/<int:wishlist_id>')
@login_required
def remove_from_wishlist(wishlist_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM wishlist WHERE id = %s AND user_id = %s',
                       (wishlist_id, session['user_id']))
        mysql.connection.commit()
        cursor.close()
        flash('Item removed from wishlist!', 'success')
    except Exception as e:
        logger.error(f"Error in remove_from_wishlist route: {e}")
        flash('An error occurred while removing from wishlist!', 'error')
    return redirect(url_for('wishlist'))

if __name__ == '__main__':
    app.run(debug=True)