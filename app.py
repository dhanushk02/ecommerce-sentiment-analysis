import os
import bcrypt
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename

from database import execute_select, execute_insert, execute_update, execute_delete, check_admin_login, check_user_login

import joblib
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from textblob import TextBlob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR, "models", "sentiment_model.pkl"))
vectorizer = joblib.load(os.path.join(BASE_DIR, "models", "tfidf_vectorizer.pkl"))

os.makedirs("static/uploads", exist_ok=True)

# # Download necessary NLTK data (only the first time)
# nltk.download('punkt_tab')
# nltk.download('stopwords')
# nltk.download('wordnet')

# import nltk
# nltk.data.path.append('./.venv/nltk_data')  # Add custom download path

# nltk.download('punkt', download_dir='./.venv/nltk_data')

# nltk.download('punkt_tab', download_dir='./.venv/nltk_data')
# nltk.download('stopwords', download_dir='./.venv/nltk_data')
# nltk.download('wordnet', download_dir='./.venv/nltk_data')

# ---------------- NLP SETUP ----------------
import nltk

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
stop_words.discard('not')  # Ensure "not" is not removed


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")



# Home route

from functools import wraps

def admin_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin login required", "warning")
            return redirect(url_for("login", tab="admin"))
        return f(*args, **kwargs)
    return wrap

def user_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "id" not in session:
            flash("Login required", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/login')
def login():
    active_tab = 'user'  # Default to user tab

    # If a tab is passed in the request, use it
    if request.args.get('tab') == 'admin':
        active_tab = 'admin'

    return render_template('login.html', active_tab=active_tab)



@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    active_tab = 'admin'  # Default to 'admin' tab
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        success, error_message = check_admin_login(email, password)

        if success:
            flash('Logged in successfully!', 'success')
            return redirect(url_for('adminhome'))
        else:
            flash(error_message or 'Invalid login attempt. Please try again.', 'danger')

    return render_template('login.html', active_tab=active_tab)



@app.route('/adminhome')
@admin_login_required
def adminhome():
    return render_template('Admin/AdminHome.html')



@app.route('/AdminCategoriesList', methods=['GET'])
@admin_login_required
def AdminCategoriesList():
    categories = execute_select("SELECT * FROM tblcategories ORDER BY id DESC")
    return render_template('Admin/AdminCategoriesList.html', categories=categories)


@app.route('/AdminCategoriesAdd', methods=['POST'])
@admin_login_required
def AdminCategoriesAdd():
    name = request.form.get('name', '').strip()

    if not name:
        flash("Category name is required.", "danger")
    else:
        existing = execute_select("SELECT * FROM tblcategories WHERE Category = ?", (name,))
        if existing:
            flash("Category already exists.", "warning")
        else:
            result = execute_insert("INSERT INTO tblcategories (Category) VALUES (?)", (name,))
            if result == True:
                flash("Category added successfully!", "success")
            else:
                flash(f"Failed to add category: {result}", "danger")
    return redirect(url_for('AdminCategoriesList'))


@app.route('/AdminCategoriesDelete/<int:id>', methods=['POST'])
@admin_login_required
def AdminCategoriesDelete(id):
    result = execute_delete("DELETE FROM tblcategories WHERE id = ?", (id,))
    if "deleted" in result:
        flash(result, "info")
    else:
        flash(result, "danger")
    return redirect(url_for('AdminCategoriesList'))



UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/AdminProductsList', methods=['GET'])
@admin_login_required
def AdminProductsList():
    category_id = request.args.get('category')
    query = """
        SELECT p.*, c.Category AS category_name
        FROM tblproducts p
        JOIN tblcategories c ON p.category_id = c.id
    """
    params = []
    if category_id:
        query += " WHERE p.category_id = ?"
        params.append(category_id)
    query += " ORDER BY p.id DESC"

    products = execute_select(query, tuple(params))
    categories = execute_select("SELECT id, Category FROM tblcategories ORDER BY Category")
    
    return render_template('Admin/AdminProductList.html', products=products, categories=categories)


@app.route('/AdminProductDetails', methods=['GET', 'POST'])
@admin_login_required
def AdminProductDetails():
    product_id = request.args.get('id')
    product = None

    if product_id:
        product = execute_select("SELECT * FROM tblproducts WHERE id = ?", (product_id,))
        if product:
            product = product[0]
        else:
            flash("Product not found", "danger")
            return redirect(url_for('Admin/AdminProductsList'))

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category_id = request.form['category_id']
        description = request.form['description']
        image = request.files['image']

        filename = product['image'] if product else None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if product:
            # Update
            query = """
                UPDATE tblproducts SET name=?, price=?, category_id=?, description=?, image=? WHERE id=?
            """
            execute_update(query, (name, price, category_id, description, filename, product_id))
            flash("Product updated successfully", "success")
        else:
            # Insert
            query = """
                INSERT INTO tblproducts (name, price, category_id, description, image) VALUES (?, ?, ?, ?, ?)
            """
            execute_insert(query, (name, price, category_id, description, filename))
            flash("Product added successfully", "success")

        return redirect(url_for('AdminProductsList'))

    categories = execute_select("SELECT * FROM tblcategories")
    return render_template('Admin/AdminProductDetails.html', product=product, categories=categories)

@app.route('/AdminProductDelete/<int:id>', methods=['POST'])
@admin_login_required
def AdminProductDelete(id):
    msg = execute_delete("DELETE FROM tblproducts WHERE id = ?", (id,))
    flash(msg, "success" if "deleted" in msg.lower() else "danger")
    return redirect(url_for('AdminProductsList'))




@app.route('/AdminOrdersList', methods=['GET'])
@admin_login_required
def AdminOrdersList():
    status_filter = request.args.get('status')
    
    query = """
        SELECT o.id, o.status, o.order_date, o.quantity, o.address,
               u.name AS user_name,
               p.name AS product_name
        FROM tblorders o
        JOIN tblusers u ON o.user_id = u.id
        JOIN tblproducts p ON o.product_id = p.id
    """
    params = []
    if status_filter:
        query += " WHERE o.status = ?"
        params.append(status_filter)
    query += " ORDER BY o.order_date DESC"

    orders = execute_select(query, tuple(params))

    # Get distinct statuses for the filter dropdown
    status_query = "SELECT DISTINCT status FROM tblorders"
    status_rows = execute_select(status_query)
    statuses = [row['status'] for row in status_rows]

    return render_template('Admin/AdminOrdersList.html', orders=orders, statuses=statuses)


@app.route('/AdminDeleteOrder/<int:id>', methods=['POST'])
@admin_login_required
def AdminDeleteOrder(id):
    try:
        query = "DELETE FROM tblorders WHERE id = ?"
        params = (id,)
        message = execute_delete(query, params)
        
        # Flash success or error message
        flash(message, 'success' if "deleted" in message else 'danger')
        
        return redirect(url_for('AdminOrdersList'))  # Redirect to orders list page
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')
        return redirect(url_for('AdminOrdersList'))
    


@app.route('/AdminOrderDetails/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def AdminOrderDetails(id):
    if request.method == 'POST':
        new_status = request.form.get('status')
        update_query = "UPDATE tblorders SET status = ? WHERE id = ?"
        execute_update(update_query, (new_status, id))
        flash("Order status updated successfully.", "success")
        return redirect(url_for('AdminOrdersList'))

    # Select full order with user & product info
    select_query = """
        SELECT o.id, o.status, o.order_date, o.quantity, o.address,
               u.name AS user_name, u.email,
               p.name AS product_name, p.price
        FROM tblorders o
        JOIN tblusers u ON o.user_id = u.id
        JOIN tblproducts p ON o.product_id = p.id
        WHERE o.id = ?
    """
    result = execute_select(select_query, (id,))
    order = result[0] if result else None

    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('AdminOrdersList'))

    return render_template('Admin/AdminOrderDetails.html', order=order)


@app.route('/AdminUsersList', methods=['GET'])
@admin_login_required
def AdminUsersList():
    query = "SELECT id, name, email, created_at FROM tblusers ORDER BY created_at DESC"
    users = execute_select(query)
    return render_template('Admin/AdminUsersList.html', users=users)

@app.route('/AdminUserDelete/<int:id>', methods=['POST'])
@admin_login_required
def AdminUserDelete(id):
    try:
        query = "DELETE FROM tblusers WHERE id = ?"
        execute_delete(query, (id,))
        flash("User deleted successfully.", "success")
    except Exception as e:
        print("Delete error:", e)
        flash("An error occurred while deleting the user.", "danger")
    return redirect(url_for('AdminUsersList'))




@app.route('/AdminProductListReview', methods=['GET'])
@admin_login_required
def AdminProductListReview():
    category_id = request.args.get('category')
    query = """
        SELECT p.*, c.Category AS category_name
        FROM tblproducts p
        JOIN tblcategories c ON p.category_id = c.id
    """
    params = []
    if category_id:
        query += " WHERE p.category_id = ?"
        params.append(category_id)
    query += " ORDER BY p.id DESC"

    products = execute_select(query, tuple(params))
    categories = execute_select("SELECT id, Category FROM tblcategories ORDER BY Category")
    
    return render_template('Admin/AdminProductListReview.html', products=products, categories=categories)



@app.route('/AdminReviewList/<int:id>')
@admin_login_required
def AdminReviewList(id):
    # Fetch the product
    product = execute_select("""
        SELECT p.*, c.Category 
        FROM tblproducts p 
        JOIN tblcategories c ON p.category_id = c.id 
        WHERE p.id = ?
    """, (id,))

    if not product:
        return "Product not found", 404

    # Fetch product reviews
    reviews = execute_select("""
        SELECT r.*, u.name 
        FROM tblreviews r
        JOIN tblusers u ON r.user_id = u.id
        WHERE r.product_id = ?
        ORDER BY r.created_at DESC
    """, (id,))

    # Print reviews to debug
    print(reviews)  # Debugging line

    # Pass product and reviews to the template
    return render_template("Admin/AdminReviewList.html", product=product[0], reviews=reviews)



@app.route('/AdminDeleteReview/<int:review_id>/<int:product_id>', methods=['POST'])
@admin_login_required
def AdminDeleteReview(review_id, product_id):
    try:
        query = "DELETE FROM tblreviews WHERE id = ?"
        execute_delete(query, (review_id,))
        flash('Review deleted successfully.', 'success')
    except Exception as e:
        print("Error deleting review:", e)
        flash('Failed to delete review.', 'danger')
    
    return redirect(url_for('AdminReviewList', id=product_id))


# User logout route
@app.route('/adminlogout')
@admin_login_required
def adminlogout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('login'))




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match", "danger")
        else:
            existing = execute_select("SELECT * FROM tblusers WHERE email = ?", (email,))
            if existing:
                flash("Email already registered", "warning")
            else:
                # Hash the password before saving
                hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                result = execute_insert(
                    "INSERT INTO tblusers (name, email, password) VALUES (?, ?, ?)",
                    (name, email, hashed_password)
                )
                if result == True:
                    flash("Registration successful! Please log in.", "success")
                    return redirect(url_for('login'))
                else:
                    flash("Error occurred during registration.", "danger")

    return render_template("register.html")


@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    active_tab = 'user'  # Default to 'admin' tab
    if request.method == 'POST':
        email = request.form['useremail']
        password = request.form['userpassword']

        success, error_message = check_user_login(email, password)

        if success:
            flash('Logged in successfully!', 'success')
            return redirect(url_for('userhome'))
        else:
            flash(error_message or 'Invalid login attempt. Please try again.', 'danger')

    return render_template('login.html', active_tab=active_tab)


@app.route('/userhome')
def userhome():
    return render_template('User/UserHome.html')




@app.route('/UserProductsList')
def UserProductsList():
    # Retrieve filter parameters from the request
    category_id = request.args.get('category')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    # Debugging: Check values coming from request args
    print(f"Category ID from request: {category_id}")
    print(f"Min Price: {min_price}")
    print(f"Max Price: {max_price}")

    # Base query
    query = """
        SELECT p.id, p.name, p.price, p.image,
               COALESCE(SUM(CASE WHEN r.sentiment = 'positive' THEN 1 ELSE 0 END), 0) AS positive_reviews,
               COALESCE(SUM(CASE WHEN r.sentiment = 'neutral' THEN 1 ELSE 0 END), 0) AS neutral_reviews,
               COALESCE(SUM(CASE WHEN r.sentiment = 'negative' THEN 1 ELSE 0 END), 0) AS negative_reviews
        FROM tblproducts p
        LEFT JOIN tblreviews r ON p.id = r.product_id
        WHERE 1=1
    """

    # Apply category filter if provided
    if category_id:
        query += " AND p.category_id = ?"
    
    # Apply price range filter if provided
    if min_price:
        query += " AND p.price >= ?"
    if max_price:
        query += " AND p.price <= ?"

    query += " GROUP BY p.id"

    # Prepare parameters
    params = []
    if category_id:
        params.append(category_id)
    if min_price:
        params.append(min_price)
    if max_price:
        params.append(max_price)

    # Debugging: Check the query and params before execution
    print(f"Executing query: {query}")
    print(f"Parameters: {params}")

    # Execute query and retrieve filtered products
    products = execute_select(query, params)

    # Retrieve categories for the dropdown
    categories_query = "SELECT id, Category FROM tblcategories"
    categories = execute_select(categories_query)

    # Debugging: Check categories fetched from the database
    print(f"Categories fetched: {categories}")

    # Render the template with filtered products and categories
    return render_template('User/UserProductsList.html', products=products, categories=categories, selected_category=category_id)



@app.route('/UserProductDetail/<int:id>')
def UserProductDetail(id):
    # Fetch the product
    product = execute_select("""
        SELECT p.*, c.Category 
        FROM tblproducts p 
        JOIN tblcategories c ON p.category_id = c.id 
        WHERE p.id = ?
    """, (id,))

    if not product:
        return "Product not found", 404

    # Fetch product reviews
    reviews = execute_select("""
        SELECT r.*, u.name 
        FROM tblreviews r
        JOIN tblusers u ON r.user_id = u.id
        WHERE r.product_id = ?
        ORDER BY r.created_at DESC
    """, (id,))

    # Print reviews to debug
    print(reviews)  # Debugging line

    # Pass product and reviews to the template
    return render_template("User/UserProductDetail.html", product=product[0], reviews=reviews)



# Preprocess input review
def PreProcessText(review):
    if isinstance(review, str):
        tokens = word_tokenize(review.lower())
        tokens = [lemmatizer.lemmatize(word) for word in tokens if word.isalnum() and word not in stop_words]
        return ' '.join(tokens)
    return ''

# Predict sentiment using saved model
def predict_sentiment(review):
    processed = PreProcessText(review)
    vectorized = vectorizer.transform([processed])
    prediction = model.predict(vectorized)
    return prediction[0]

# Detect emotion using TextBlob
def detect_emotion(review):
    blob = TextBlob(review)
    polarity = blob.sentiment.polarity
    if polarity > 0.5:
        return "Happy"
    elif polarity > 0:
        return "Neutral-Happy"
    elif polarity < -0.5:
        return "Sad"
    elif polarity < 0:
        return "Angry"
    else:
        return "Neutral"



@app.route('/UserPostReview/<int:product_id>', methods=['GET', 'POST'])
@user_login_required
def UserPostReview(product_id):

    # Fetch the product details by product_id
    product = execute_select("""
        SELECT * FROM tblproducts WHERE id = ?
    """, (product_id,))

    # Ensure the product exists
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('UserProductsList'))  # Redirect if the product doesn't exist

    product = product[0]  # If execute_select returns a list, we need the first item (the product)

    # Handle POST request (review submission)
    if request.method == 'POST':
        review_text = request.form['review_text']
     
        sentiment = predict_sentiment(review_text)
        emotion = detect_emotion(review_text)
        
        
        # Insert the review into the database
        query = """
            INSERT INTO tblreviews (product_id, user_id, review_text, sentiment, emotion)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
        int(product_id), int(session['id']), str(review_text), str(sentiment), str(emotion) )

        result = execute_insert(query, params)
        
        print(result)
        
        if result:
            flash("Review submitted successfully!", "success")
        else:
            flash("Failed to submit review. Please try again.", "danger")

        return redirect(url_for('UserProductDetail', id=product_id))

    # Render the review form (GET request)
    return render_template("User/UserPostReview.html", product=product)




@app.route('/UserPlaceOrder/<int:product_id>', methods=['POST'])
@user_login_required
def UserPlaceOrder(product_id):
    user_id = session.get('id')

    quantity = request.form.get('quantity', 1)
    address = request.form.get('address')

    # Basic validation
    if not address or int(quantity) < 1:
        flash("Invalid order details.", "danger")
        return redirect(url_for('UserProductsList'))

    query = """
        INSERT INTO tblorders (user_id, product_id, quantity, address, status)
        VALUES (?, ?, ?, ?, ?)
    """
    params = (user_id, product_id, quantity, address, 'Pending')
    result = execute_insert(query, params)

    if result == True:
        flash("Order placed successfully!", "success")
    else:
        flash(f"Failed to place order: {result}", "danger")

    return redirect(url_for('UserProductsList'))




@app.route('/UserOrdersList', methods=['GET'])
@user_login_required
def UserOrdersList():
    user_id = session.get('id')
    
    # Query to fetch the user's orders
    query = """
        SELECT o.id, o.product_id, o.quantity, o.address, o.status, o.order_date, p.name, p.price
        FROM tblorders o
        JOIN tblproducts p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.order_date DESC
    """
    params = (user_id,)
    orders = execute_select(query, params)

    return render_template('User/UserOrdersList.html', orders=orders)




@app.route('/UserChangePassword', methods=['GET', 'POST'])
@user_login_required
def UserChangePassword():
    user_id = session.get('id')

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Fetch current hashed password
        query = "SELECT password FROM tblusers WHERE id = ?"
        result = execute_select(query, (user_id,))
        if not result:
            flash("User not found.", "danger")
            return redirect(url_for('UserChangePassword'))

        stored_hashed = result[0]['password']

        if not bcrypt.checkpw(old_password.encode('utf-8'), stored_hashed.encode('utf-8')):
            flash("Old password is incorrect.", "danger")
            return redirect(url_for('UserChangePassword'))

        if new_password != confirm_password:
            flash("New passwords do not match.", "warning")
            return redirect(url_for('UserChangePassword'))

        new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        update_query = "UPDATE tblusers SET password = ? WHERE id = ?"
        update_result = execute_update(update_query, (new_hashed, user_id))

        if update_result == True:
            flash("Password changed successfully!", "success")
        else:
            flash("Failed to update password.", "danger")

        return redirect(url_for('UserChangePassword'))

    return render_template('User/UserChangePassword.html')



# User logout route
@app.route('/userlogout')
@user_login_required
def userlogout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('login'))


# Run the app
if __name__ == '__main__':
    app.run()
