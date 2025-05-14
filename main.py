from flask import Flask, render_template, request, jsonify, flash, redirect, session, url_for, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine, text, Float
from enum import IntEnum, Enum
import random
import bcrypt
import mysql.connector
from datetime import datetime, timezone
from sqlalchemy.types import Enum as SQLAlchemyEnum
from decimal import Decimal
from werkzeug.utils import secure_filename
import os
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='cset155',
        database='ecommerce_application'
    )
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

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
    balance = db.Column(db.Numeric(10, 2), default=0.00)

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    vendor = db.Column(db.String(50), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
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


class Orders(db.Model):
    __tablename__ = 'orders'

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = db.Column(SQLAlchemyEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_price = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)


class CartItem(db.Model):
    cart_item_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, server_default=db.func.now())

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    vendor_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), nullable=False, default='pending')
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    reviewers_name = db.Column(db.String(50))
    rating = db.Column(db.Integer, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    image = db.Column(db.String(255))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)

class PendingReturn(db.Model):
    return_id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    demand_specification = db.Column(db.String(30), nullable=False)
    images = db.Column(db.String(255))
    title = db.Column(db.String(60), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(11), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))

class Chat(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.Text)
    images = db.Column(db.String(255))
    return_id = db.Column(db.Integer, db.ForeignKey('pending_return.return_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))

class ChatMessage(db.Model):
    __tablename__ = 'ChatMessage'

    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.chat_id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

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
    return render_template('product_page.html')



@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        flash("Please log in to submit a complaint.", "error")
        return redirect(url_for('login'))

    title = request.form['title']
    description = request.form['description']
    demand_spec = request.form['demand_specification']
    product_id = request.form['product_id']
    order_id = request.form['order_id']
    user_id = session['user_id']
    date = datetime.now()
    image_path = None

    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            filename = secure_filename(image.filename)
            image_path = os.path.join('static/uploads', filename)
            image.save(image_path)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Pending_Return (title, description, demand_specification, date, status, images, user_id, order_id, product_id)
        VALUES (%s, %s, %s, %s, 'pending', %s, %s, %s, %s)
    """, (title, description, demand_spec, date, image_path, user_id, order_id, product_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Complaint submitted successfully.", "success")
    return redirect(url_for('accounts'))

@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('cart.html', user_id=session['user_id'])

@app.route('/chats')
def chats():
    return render_template('chats.html')

@app.route("/api/cart")
def cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(session['user_id'])
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


@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({'message': 'Not logged in'}), 401

    data = request.get_json()
    user_id = session['user_id']

    for item in data['items']:
        product_id = item['product_id']
        quantity = item['quantity']

        existing_item = db.execute(
            "SELECT * FROM cart_item WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        ).fetchone()

        if existing_item:
            db.execute(
                "UPDATE cart_item SET quantity = %s WHERE user_id = %s AND product_id = %s",
                (quantity, user_id, product_id)
            )
        else:
            db.execute(
                "INSERT INTO cart_item (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                (user_id, product_id, quantity)
            )

    db.commit()
    return jsonify({'message': 'Cart updated successfully'})


@app.route('/get_cart')
def get_cart():
    if 'user_id' not in session:
        return jsonify([])

    user_id = session['user_id']
    cart_items = db.execute("""
        SELECT cart_item.product_id, cart_item.quantity, Product.name, Product.price, Product.images
        FROM cart_item
        JOIN Product ON cart_item.product_id = Product.product_id
        WHERE cart_item.user_id = %s
    """, (user_id,)).fetchall()

    return jsonify([dict(item) for item in cart_items])


@app.route('/request_return/<int:order_id>', methods=['POST'])
def request_return(order_id):
    if 'username' not in session:
        return redirect('/login')

    user = User.query.filter_by(username=session['username']).first()
    order = Orders.query.filter_by(order_id=order_id, user_id=user.user_id).first()

    if not order:
        flash("Invalid order for return", "error")
        return redirect('/account')

    reason = request.form['return_reason']
    product_id = request.form.get('product_id')
    product_title = request.form.get('product_title')

    return_request = PendingReturn(
        title=f"Return Request for {product_title}",
        description=reason,
        demand_specification="Return",  # hardcoded
        images="",
        customer_comment="",
        date=datetime.now(),
        status="pending",
        user_id=user.user_id,
        order_id=order_id,
        product_id=product_id
    )

    db.session.add(return_request)
    db.session.commit()

    flash("Return request submitted for admin review.", "success")
    return redirect('/my_orders')

@app.route('/approve_return/<int:return_id>', methods=['POST'])
def approve_return(return_id):
    if 'user_type' not in session or session['user_type'] not in [2, 3]:
        return redirect('/login')

    ret = PendingReturn.query.get_or_404(return_id)
    ret.status = 'approved'
    db.session.commit()
    flash("Return approved.", "success")
    return redirect('/admin_returns')


@app.route('/deny_return/<int:return_id>', methods=['POST'])
def deny_return(return_id):
    if 'user_type' not in session or session['user_type'] not in [2, 3]:
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
        raw_orders = Orders.query.filter_by(user_id=user.user_id).all()
        returns = PendingReturn.query.filter_by(user_id=user.user_id).all()

        order_data = []
        for order in raw_orders:
            product = Product.query.get(order.product_id)
            order_data.append({
                "order_id": order.order_id,
                "product_id": order.product_id,
                "product_title": product.name if product else "Unknown Product"
            })

        return render_template('accounts.html', user=user, orders=order_data, returns=returns)

    # Admin or Vendor view
    user_type = request.args.get('type', 'Vendor')
    if user_type.lower() not in ['vendor', 'admin']:
        user_type = 'Vendor'

    users = User.query.filter_by(user_type=2 if user_type.lower() == 'vendor' else 3).all()
    return render_template('accounts.html', user=user, users=users)


@app.route('/returns', methods=['GET', 'POST'])
def returns():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        demand = request.form['demand']
        image = request.form['image'] 
        comment = request.form.get('comment') 
        status = "pending"
        new_return = PendingReturn(
            title=title,
            description=description,
            demand_specification=demand,
            images=image,
            customer_comment=comment,
            date=datetime.now(),
            status=status
        )
        db.session.add(new_return)
        db.session.commit()
        flash("Return request submitted for admin approval.", "success")
        return redirect('/returns')
    return render_template('accounts.html')


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
            print("Current session user_id:", session.get('user_id'))

            
            cart_items = (
                db.session.query(
                    CartItem.product_id,
                    CartItem.quantity,
                    Product.name,
                    Product.price,
                    Product.images
                )
                .join(Product, CartItem.product_id == Product.product_id)
                .filter(CartItem.user_id == user.user_id)
                .all()
            )

            session['cart'] = [dict(zip(
                ['product_id', 'quantity', 'name', 'price', 'images'],
                item
            )) for item in cart_items]

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
                    return redirect('/product_creation')
                else:
                    return redirect('/admin_returns')
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

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return render_template('login.html')

@app.route('/vendor_admin_signup', methods=['GET', 'POST'])
def vendor_admin_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        user_type = int(request.form['user_type'])  # 2 = vendor, 3 = admin

        if not all([name, email, username, password]):
            flash("All fields are required", "error")
            return redirect('/vendor_admin_signup')

        if user_type not in [2, 3]:
            flash("Invalid account type", "error")
            return redirect('/vendor_admin_signup')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists", "error")
            return redirect('/vendor_admin_signup')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            name=name,
            email=email,
            username=username,
            password=hashed_password,
            user_type=user_type
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect('/login')

    return render_template('vendor_admin_signup.html')


@app.route('/product_creation')
def product_creation():
    return render_template('product_creation.html')


@app.route('/product_page')
def product_page():
    return render_template('product_page.html')

@app.route('/product_detail')
def product_detail():
    return render_template("product_detail.html")

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Or show a message

    user_id = session['user_id']

    # Only load this user's orders
    receipts = Receipt.query.filter_by(user_id=user_id).all()
    orders_with_images = []

    for receipt in receipts:
        product = Product.query.get(receipt.product_id)
        orders_with_images.append({
            "product_id": receipt.product_id,
            "product_title": receipt.product_title,
            "quantity_item": receipt.quantity_item,
            "date_purchased": receipt.date_purchased,
            "total_price": receipt.total_price,
            "image_url": product.images if product else "/static/default.jpg"
        })

    return render_template("my_orders.html", orders=orders_with_images)


@app.route('/api/create_product', methods=['POST'])
def create_product():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    name = data.get("product_title")
    images = data.get("product_images")
    description = data.get("product_description")
    warranty_period = data.get("product_warranty")
    product_category = data.get("product_category")
    colors = data.get("available_colors")
    inventory_space = data.get("inventory_size")
    sizes = data.get("sizes")
    price = data.get("price")

    discount_price = None
    discount_time = None

    product = Product(
        name=name,
        vendor=session['username'],
        vendor_id=session['user_id'], 
        images=images,
        description=description,
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
    print(f"Fetched {len(products)} products")
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

@app.route('/api/product_lookup', methods=['POST'])
def product_lookup():
    data = request.get_json()
    product_name = data.get("product_name", "").strip()
    vendor_name = data.get("vendor_name", "").strip()

    query = Product.query

    if product_name:
        query = query.filter(Product.name.ilike(f"%{product_name}%"))
    if vendor_name:
        query = query.filter(Product.vendor.ilike(f"%{vendor_name}%"))

    product = query.first()

    if not product:
        return jsonify({"error": "Product not found"}), 404

    product_data = {
        "product_id": product.product_id,
        "name": product.name,
        "vendor": product.vendor,
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

        new_vendor_name = data.get("vendor")
        if new_vendor_name:
            product.vendor = new_vendor_name
            vendor_user = User.query.filter_by(username=new_vendor_name).first()
            if vendor_user:
                product.vendor_id = vendor_user.user_id
            else:
                return jsonify({"error": "Vendor username not found"}), 400
        print("Received vendor:", data.get("vendor"))
        print("Received category:", data.get("category"))

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
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    user_id = session['user_id']
    cart_items = data.get("cart", [])

    # Don't allow writing to receipt if user balance is insufficient
    user = User.query.get(user_id)
    total_cost = sum(float(item.get("price", 0)) * int(item.get("quantity", 1)) for item in cart_items)
    if Decimal(user.balance) < Decimal(str(total_cost)):
        return jsonify({"error": "Insufficient balance"}), 400

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


@app.route('/api/get_user_id')
def get_user_id():
    if 'user_id' in session:
        return jsonify({"user_id": session['user_id']})
    return jsonify({"error": "Not logged in"}), 401

@app.route('/api/sent_order', methods=['POST'])
def send_order():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    cart_items = data.get("cart", [])
    order_status = OrderStatus.PENDING

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Convert to Decimal for accurate comparison
    total_order_cost = sum(
        Decimal(str(item.get("price", "0"))) * Decimal(str(item.get("quantity", "1")))
        for item in cart_items
    )

    print("User balance:", user.balance)
    print("Total cost:", total_order_cost)

    user_balance = Decimal(str(user.balance))
    print(f"User Balance (Decimal): {user_balance}, Total Order Cost (Decimal): {total_order_cost}")
    print("TYPE CHECK — user_balance:", type(user_balance), " total_order_cost:", type(total_order_cost))
    if user_balance < total_order_cost:
        return jsonify({
            "error": "Insufficient balance to complete the purchase",
            "user_balance": str(user.balance),
            "required_total": str(total_order_cost)
        }), 400

    # Deduct balance
    user.balance = user_balance - total_order_cost

    for item in cart_items:
        item_total = Decimal(str(item.get("price", "0"))) * Decimal(str(item.get("quantity", "1")))
        product_id = item.get("product_id")

        product = Product.query.get(product_id)
        vendor_user = User.query.filter_by(username=product.vendor).first()
        vendor_id = vendor_user.user_id if vendor_user else None

        if not vendor_id:
            continue  # skip if vendor missing

        order = Orders(
            user_id=user_id,
            vendor_id=vendor_id,
            product_id=product_id,
            total_price=float(item_total),
            status=order_status
        )
        db.session.add(order)

    db.session.commit()
    return jsonify({"message": f"{len(cart_items)} item(s) sent to orders and balance updated."})


@app.route('/api/review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    rating = data.get('rating')
    image = data.get('image')
    product_id = data.get('product_id')  # ✅ must be passed from frontend

    if not all([name, description, rating, product_id]):
        return jsonify({"error": "Missing required fields"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    vendor_id = product.vendor_id

    # Check for existing review
    existing_review = Review.query.filter_by(
        reviewers_name=name,
        product_id=product_id
    ).first()
    if existing_review:
        return jsonify({"error": "You've already reviewed this product."}), 400

    review = Review(
        reviewers_name=name,
        rating=rating,
        vendor_id=vendor_id,
        description=description,
        date=datetime.now(),
        image=image,
        product_id=product_id
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review submitted successfully"})

@app.route('/api/load_reviews', methods=['GET'])
def load_reviews():
    product_id = request.args.get('id', type=int)

    if not product_id:
        return jsonify({"error": "Product ID is required"}), 400

    reviews = Review.query.filter_by(product_id=product_id).all()

    review_list = [{
        "name": review.reviewers_name,
        "rating": review.rating,
        "description": review.description,
        "date": review.date.strftime('%Y-%m-%d') if review.date else None,
        "image": review.image
    } for review in reviews]

    return jsonify(review_list)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    chat_id = data.get("chat_id")
    sender_id = session.get('user_id')
    message_text = data.get("message")

    if not all([chat_id, sender_id, message_text]):
        return jsonify({"error": "Missing required fields"}), 400

    new_message = ChatMessage(
        chat_id=chat_id,
        sender_id=sender_id,
        message_text=message_text
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully"})

@app.route('/api/get_user_chats')
def get_user_chats():
    user_id = request.args.get('user_id', type=int)
    chats = Chat.query.filter_by(user_id=user_id).all()
    return jsonify([
        {
            "chat_id": chat.chat_id,
            "name": chat.name,
            "description": chat.description
        } for chat in chats
    ])

@app.route('/api/load_messages/<int:chat_id>', methods=['GET'])
def load_messages(chat_id):
    messages = ChatMessage.query.filter_by(chat_id=chat_id).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify([
        {
            "sender_id": msg.sender_id,
            "message": msg.message_text,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M')
        }
        for msg in messages
    ])

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")
    description = data.get("description")

    new_chat = Chat(
        name=name,
        description=description,
        user_id=user_id,
        images="",
        return_id=None
    )
    db.session.add(new_chat)
    db.session.commit()

    initial_msg = ChatMessage(
        chat_id=new_chat.chat_id,
        sender_id=user_id,
        message_text=description
    )
    db.session.add(initial_msg)
    db.session.commit()

    return jsonify({"message": "Chat created successfully", "chat_id": new_chat.chat_id})

if __name__ == '__main__':
        app.run(debug=True)