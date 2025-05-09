from flask import Flask, render_template, request, jsonify, flash, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text, Float
from enum import IntEnum
import random
import bcrypt
import mysql.connector
from datetime import datetime, timezone

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

class Receipt(db.Model):
    __tablename__ = 'receipt'

    receipt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    product_title = db.Column(db.String(50), nullable=False)
    quantity_item = db.Column(db.Integer, nullable=False)
    date_purchased = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Optional: relationships if you have User and Product models
    user = db.relationship('User', backref='receipts')
    product = db.relationship('Product', backref='receipts')


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

@app.route("/api/cart")
def cart():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(username=session['username']).first()
    cart_items = CartItem.query.filter_by(user_id=user.user_id).all()

    result = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        result.append({
            "product_id": product.product_id,
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

@app.route('/account', methods=['GET', 'POST'])
def accounts():
    user_type = request.args.get('type', 'Vendor')  
    if user_type.lower() not in ['vendor', 'admin']:
        user_type = 'Vendor'  
    users = User.query.filter_by(role=user_type.capitalize()).all()
    return render_template('accounts.html', users=users, selected_type=user_type.capitalize())

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

@app.route('/api/complete_order', methods=['POST'])
def complete_order():
    data = request.json  # should contain items, user info, etc.

    # Save to database (e.g., create a Receipt record)
    # Example:
    # for item in data['cart']:
    #     new_receipt = Receipt(user_id=data['user_id'], product_id=item['product_id'], quantity=item['quantity'], ...)
    #     db.session.add(new_receipt)

    db.session.commit()
    return jsonify({"message": "Order saved to receipts!"})

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
            "vendor": product.vendor,
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
@app.route('/api/receipt', methods=['POST'])
def export_cart():
    data = request.get_json()
    user_id = data.get("user_id")
    cart_items = data.get("cart", [])

    for item in cart_items:
        item_total = float(item.get("price", 0)) * int(item.get("quantity", 1))
        new_receipt = Receipt(
            user_id=user_id,
            product_id=item.get("product_id"),
            product_title=item.get("product_title"),
            quantity_item=item.get("quantity"),
            total_price=item_total
        )
        db.session.add(new_receipt)

    db.session.commit()

    return jsonify({"message": f"{len(cart_items)} item(s) saved to receipt."})
@app.route('api/unconfirmed', methods=['POST'])
def export_unconfirmed():
    data = request.get_json()
    user_id = data.get("user_id")
    cart_items = data.get("cart", [])
    order_status = "Unconfirmed"

    for item in cart_items:
        order = UnconfirmedOrder(
            user_id=user_id,
            product_id=item.get("product_id"),
            product_title=item.get("product_title"),
            quantity_item=item.get("quantity"),
            price=item.get("price"),
            order_status=order_status
        )
# order_id = db.Column(db.Integer, primary_key=True)
# user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
# vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
# date = db.Column(db.DateTime, nullable=False)
# items = db.Column(db.String(255), nullable=False)
# price = db.Column(db.Integer, nullable=False)
# order_status = db.Column(db.String(15), nullable=False)

if __name__ == '__main__':
        app.run(debug=True)