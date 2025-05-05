from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text, Float
from enum import IntEnum
import random
import bcrypt
import mysql.connector
conn_str = "mysql://root:cset155@localhost/ecommerce_application"
engine = create_engine(conn_str, echo = True)
conn = engine.connect()

app = Flask(__name__)

# Setup MySQL connection for Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:cset155@localhost/ecommerce_application"
app.config['SECRET_KEY'] = 'mysecretkey123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    username = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.SmallInteger, nullable=False)  # 1 = customer, 2 = vendor, 3 = admin


class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    warranty_period = db.Column(db.String(20))
    category = db.Column(db.String(50))
    images = db.Column(db.String(255), nullable=False)
    colors = db.Column(db.String(50), nullable=False)
    sizes = db.Column(db.String(50), nullable=False)
    inventory_space = db.Column(db.Integer, nullable=False)
    price = db.Column(Float, nullable=False)
    discount_price = db.Column(Float)
    discount_time = db.Column(db.DateTime)


class UnconfirmedOrder(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    items = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(15), nullable=False)


class CartItem(db.Model):
    cart_item_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, server_default=db.func.now())


class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    reviewers_name = db.Column(db.String(50))
    rating = db.Column(db.Integer, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    image = db.Column(db.String(255))


class PendingReturn(db.Model):
    return_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    demand_specification = db.Column(db.String(30), nullable=False)
    images = db.Column(db.String(255))
    title = db.Column(db.String(60), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(11), nullable=False)


class Chat(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    images = db.Column(db.String(255))
    return_id = db.Column(db.Integer, db.ForeignKey('pending_return.return_id'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/account', methods=['GET', 'POST'])
def accounts():
    return render_template('accounts.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error = "Both fields (Username and Password) are required"
            return render_template('login.html', error=error)

        user_account = User.query.filter_by(username=username).first()
        if user_account and bcrypt.checkpw(password.encode('utf-8'), user_account.password.encode('utf-8')):
            session['username'] = username
            session['account_type'] = 'user'
            session['password'] = password  

            return redirect('/accounts') 

        error = "Invalid username or password"
        return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 1)  

        if not name or not email or not username or not password:
            flash("All fields are required", "error")
            return redirect('/signup') 

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists", "error")
            return redirect('/signup')  

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            name=name,
            email=email,
            username=username,
            password=hashed_password,
            user_type=int(user_type)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect('/login')  
    return render_template('signup.html')

@app.route('/vendor_signup')
def vendor_signup():
    return render_template('vendor_signup')

@app.route('/vendor_login')
def vendor_login():
    return render_template('vendor_login')


@app.route('/product_creation')
def product_creation():
    return render_template('product_creation.html')

@app.route('/product_page')
def product_page():
    return render_template('product_page.html')


@app.route('/api/create_product', methods=['POST'])
def create_product():
    data = request.get_json()

    name = data.get("product_title")
    vendor = data.get("vendor")
    images = data.get("product_images")
    description = data.get("product_description")
    warranty_period = data.get("product_warranty")
    product_category = data.get("product_category")
    colors = data.get("available_colors")
    inventory_space = data.get("inventory_size")
    sizes = data.get("sizes")
    price = data.get("price")
    
    # Default values for now — update these if you want full support later
    discount_price = None
    discount_time = None

    product = Product(
        name=name,
        images=images,
        description=description,
        vendor=vendor,
        warranty_period=warranty_period,
        category=product_category,
        colors=colors,
        sizes=sizes,
        inventory_space=int(inventory_space),
        price=float(price),
        discount_price=discount_price,
        discount_time=discount_time
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product Created Successfully", "product": product.name})

@app.route('/api/get_products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_list.append({
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "warranty_period": product.warranty_period,
            "category": product.category,
            "images": product.images,
            "colors": product.colors,
            "sizes": product.sizes,
            "inventory_space": product.inventory_space,
            "price": product.price,
            "discount_price": product.discount_price,
            "discount_time": product.discount_time.isoformat() if product.discount_time else None
        })

    return jsonify({"products": product_list})

@app.route('/api/product/<int:product_id>', methods=["GET", "PUT"])
def get_or_update_product(product_id):
    # Edit Functionality
    if request.method == "PUT":
        data = request.get_json()
        product = Product.query.get_or_404(product_id)

        product.name = data.get("name")
        product.description = data.get("description")
        product.warranty_period = data.get("warranty_period")
        product.category = data.get("category")
        product.images = data.get("images")
        product.colors = data.get("colors")
        product.sizes = data.get("sizes")
        product.inventory_space = int(data.get("inventory_space"))
        product.price = float(data.get("price"))
        product.discount_price = float(data["discount_price"]) if data.get("discount_price") else None

        db.session.commit()
        return jsonify({"message": "Product updated successfully"})

    # GET fallback
    product = Product.query.get_or_404(product_id)
    product_data = {
        "product_id": product.product_id,
        "name": product.name,
        "description": product.description,
        "warranty_period": product.warranty_period,
        "category": product.category,
        "images": product.images,
        "colors": product.colors,
        "sizes": product.sizes,
        "inventory_space": product.inventory_space,
        "price": product.price,
        "discount_price": product.discount_price,
        "discount_time": product.discount_time.isoformat() if product.discount_time else None
    }
    return jsonify(product_data)


if __name__ == '__main__':
        app.run(debug=True)