from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text
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
    description = db.Column(db.Text, nullable=False)
    warranty_period = db.Column(db.String(20))
    images = db.Column(db.String(255), nullable=False)
    colors = db.Column(db.String(50), nullable=False)
    sizes = db.Column(db.String(50), nullable=False)
    inventory_space = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    discount_price = db.Column(db.Integer)
    discount_time = db.Column(db.DateTime)


class UnconfirmedOrder(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    items = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    order_status = db.Column(db.String(15), nullable=False)


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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
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
        return redirect('/login')  # or wherever you'd like
    return render_template('signup.html')

@app.route('/vendor_signup')
def vendor_signup():
    return render_template('vendor_signup')

@app.route('/product_creation')
def product_creation():
    return render_template('product_creation.html')

@app.route('/api/create_product', methods=['POST'])
def create_product():
    data = request.get_json()

    name = data.get("product_title")
    description = data.get("product_description")
    warranty_period = data.get("product_warranty")  # Optional
    colors = data.get("available_colors")
    inventory_space = data.get("inventory_size")
    sizes = data.get("sizes")
    price = data.get("price")
    
    # Default values for now — update these if you want full support later
    images = "default.jpg"  # You can replace this with actual image handling
    discount_price = None
    discount_time = None

    product = Product(
        name=name,
        description=description,
        warranty_period=warranty_period,
        images=images,
        colors=colors,
        sizes=sizes,
        inventory_space=int(inventory_space),
        price=int(price),
        discount_price=discount_price,
        discount_time=discount_time
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product Created Successfully", "product": product.name})


if __name__ == '__main__':
        app.run(debug=True)