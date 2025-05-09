from flask import Flask, render_template, request, jsonify, flash, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text, Float
from enum import IntEnum
import random
import bcrypt
import mysql.connector
from datetime import datetime

db = SQLAlchemy()
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

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_type' in session and session['user_type'] == 3:  
        vendors = User.query.filter_by(user_type=2, is_approved=False).all()
        return render_template('admin_dashboard.html', users=vendors)
    else:
        return redirect('/login')

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    user = User.query.get(user_id)
    if user and user.user_type == 2:  
        user.is_approved = True
        db.session.commit()
        flash("Vendor approved!", "success")
    return redirect('/admin_dashboard')

@app.route('/deny_user/<int:user_id>', methods=['POST'])
def deny_user(user_id):
    user = User.query.get(user_id)
    if user and user.user_type == 2:  
        db.session.delete(user)
        db.session.commit()
        flash("Vendor denied and deleted.", "success")
    return redirect('/admin_dashboard')

@app.route('/cart')
def view_cart():
    if 'username' not in session:
        return redirect('/login')
    return render_template('cart.html')

@app.route('/api/cart', methods=['GET'])
def cart():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.filter_by(username=session['username']).first()
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()

    result = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        result.append({
            "name": product.name,
            "price": product.price,
            "quantity": item.quantity
        })

    return jsonify({"cart": result})

@app.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    user = User.query.filter_by(username=session['username']).first()
    existing_item = CartItem.query.filter_by(user_id=user.user_id, product_id=product_id).first()

    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(user_id=user.user_id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    return jsonify({'message': 'Item added to cart'})

@app.route('/api/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    product_id = data.get('product_id')

    user = User.query.filter_by(username=session['username']).first()
    item = CartItem.query.filter_by(user_id=user.user_id, product_id=product_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item removed'})
    else:
        return jsonify({'error': 'Item not found in cart'}), 404
    
@app.route('/api/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()

    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    total_price = 0
    order_items = []

    for item in cart_items:
        product = Product.query.get(item.product_id)
        total_price += product.price * item.quantity
        order_items.append(f"{product.name} x{item.quantity}")

    new_order = UnconfirmedOrder(
        user_id=user.user_id,
        vendor_id=1,  
        date=datetime.now(),
        items=", ".join(order_items),
        price=total_price,
        order_status="pending"
    )
    db.session.add(new_order)

    
    for item in cart_items:
        db.session.delete(item)

    db.session.commit()
    return jsonify({'message': 'Checkout complete. Thank you for your purchase!'})

@app.route('/request_return/<int:order_id>', methods=['POST'])
def request_return(order_id):
    if 'username' not in session:
        return redirect('/login')

    user = User.query.filter_by(username=session['username']).first()
    order = UnconfirmedOrder.query.filter_by(order_id=order_id, user_id=user.user_id).first()

    if not order:
        flash("Invalid order for return", "error")
        return redirect('/account')

    reason = request.form['reason']
    demand = request.form['demand']

    return_request = PendingReturn(
        title=f"Return for Order #{order_id}",
        description=reason,
        demand_specification=demand,
        images="",  # Optional or add upload support later
        date=datetime.now(),
        status="pending"
    )

    db.session.add(return_request)
    db.session.commit()

    flash("Return request submitted for admin review.", "success")
    return redirect('/account') 



@app.route('/admin_returns')
def admin_returns():
    if 'user_type' not in session or session['user_type'] != 3: 
        return redirect('/login')

    returns = PendingReturn.query.order_by(PendingReturn.date.desc()).all()
    return render_template('admin_returns.html', returns=returns)

@app.route('/approve_return/<int:return_id>', methods=['POST'])
def approve_return(return_id):
    if 'user_type' not in session or session['user_type'] != 3:
        return redirect('/login')

    ret = PendingReturn.query.get_or_404(return_id)
    ret.status = 'approved'
    db.session.commit()
    flash("Return approved.", "success")
    return redirect('/admin_returns')


@app.route('/deny_return/<int:return_id>', methods=['POST'])
def deny_return(return_id):
    if 'user_type' not in session or session['user_type'] != 3:
        return redirect('/login')

    ret = PendingReturn.query.get_or_404(return_id)
    ret.status = 'denied'
    db.session.commit()
    flash("Return denied.", "warning")
    return redirect('/admin_returns')

@app.route('/account', methods=['GET', 'POST'])
def accounts():
    if 'username' not in session:
        return redirect('/login')

    user = User.query.filter_by(username=session['username']).first()

    if user.user_type == 1:
        
        orders = UnconfirmedOrder.query.filter_by(user_id=user.user_id).all()
        returns = PendingReturn.query.all()
        return render_template('accounts.html', user=user, orders=orders, returns=returns)

    
    user_type = request.args.get('type', 'Vendor')
    if user_type.lower() not in ['vendor', 'admin']:
        user_type = 'Vendor'

    users = User.query.filter_by(user_type=2 if user_type.lower() == 'vendor' else 3).all()
    return render_template('accounts.html', users=users, selected_type=user_type.capitalize())


@app.route('/returns', methods=['GET', 'POST'])
def returns():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        demand = request.form['demand']
        image = request.form['image']  
        status = "pending"
        new_return = PendingReturn(
            title=title,
            description=description,
            demand_specification=demand,
            images=image,
            date=datetime.now(),
            status=status
        )
        db.session.add(new_return)
        db.session.commit()
        flash("Return request submitted for admin approval.", "success")
        return redirect('/returns')
    return render_template('returns.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['username'] = user.username
            session['user_type'] = user.user_type
            session['user_id'] = user.user_id

            # Redirect based on user type
            if user.user_type == 1:
                return redirect('/')  
            elif user.user_type == 2:
                return redirect('/product_creation')  
            elif user.user_type == 3:
                return redirect('/admin_dashboard')  

        error = "Invalid username or password"
        return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('staff_login.html', error="Both fields are required")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            if user.user_type in [2, 3]:  
                session['username'] = user.username
                session['user_id'] = user.user_id
                session['user_type'] = user.user_type

                if user.user_type == 2:
                    return redirect('/vendor_dashboard')
                else:
                    return redirect('/admin_dashboard')
            else:
                return render_template('staff_login.html', error="Access denied for non-staff users.")
        return render_template('staff_login.html', error="Invalid username or password")

    return render_template('staff_login.html')

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


@app.route('/product_creation')
def product_creation():
    return render_template('product_creation.html')


@app.route('/product_page')
def product_page():
    return render_template('product_page.html')

@app.route('/product_detail')
def product_detail():
    return render_template("product_detail.html")


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