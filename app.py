from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import (get_all_products, get_product_by_id,
    add_product_to_db, delete_product_from_db, get_all_orders, save_order,
    upload_image, update_product_in_db)
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'charmly-secret-2026')

# ── TEMPORARY PRODUCT DATA ──
# We will replace this with real Firebase data later
# ── CATEGORIES ──
categories = [
    {
        'id': 'keychains',
        'name': 'Keychains',
        'emoji': '🔑',
        'subcategories': [
            {'id': 'keychains-singles', 'name': 'Singles', 'emoji': '🔑'},
            {'id': 'keychains-sets', 'name': 'Sets', 'emoji': '💞'},
        ]
    },
    {
        'id': 'crochet',
        'name': 'Crochet',
        'emoji': '🧶',
        'subcategories': [
            {'id': 'crochet-pouches', 'name': 'Pouches', 'emoji': '👜'},
            {'id': 'crochet-flowers', 'name': 'Flowers', 'emoji': '🌸'},
            {'id': 'crochet-toys', 'name': 'Mini Toys', 'emoji': '🧸'},
        ]
    },
    {
        'id': 'fridge-magnets',
        'name': 'Fridge Magnets',
        'emoji': '🧲',
        'subcategories': []
    },
]

# Products now come from Firebase — no temporary data needed

# ── CUSTOMER ROUTES ──

@app.route('/')
def home():
    all_products = get_all_products()
    featured = all_products[:6]
    return render_template('index.html', products=featured, categories=categories)

@app.route('/shop')
def shop():
    category = request.args.get('category', None)
    subcategory = request.args.get('subcategory', None)
    filter_type = request.args.get('filter', None)

    filtered = get_all_products()
    if category:
        filtered = [p for p in filtered if p['category'] == category]
    if subcategory:
        filtered = [p for p in filtered if p.get('subcategory') == subcategory]
    if filter_type == 'new':
        filtered = [p for p in filtered if p['badge_type'] == 'new']
    elif filter_type == 'bestseller':
        filtered = [p for p in filtered if p['badge_type'] == 'best']

    return render_template('shop.html',
        products=filtered,
        category=category,
        subcategory=subcategory,
        categories=categories)

@app.route('/product/<product_id>')
def product(product_id):
    item = get_product_by_id(product_id)
    if not item:
        return redirect(url_for('shop'))
    return render_template('product.html', product=item)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html',
        upi_id=os.getenv('UPI_ID', 'your_upi_id@bank'))

@app.route('/order-success')
def order_success():
    order_id = request.args.get('order_id', '')
    return render_template('order_success.html', order_id=order_id)

# ── ADMIN ROUTES ──

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    all_products = get_all_products()
    all_orders = get_all_orders()
    return render_template('admin/dashboard.html',
        products=all_products, categories=categories, orders=all_orders)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD', 'charmly123'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Wrong password. Try again.'
    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ── API ROUTES (used by JavaScript) ──

@app.route('/api/products')
def api_products():
    return jsonify(products)

@app.route('/api/product/<product_id>')
def api_product(product_id):
    item = next((p for p in products if p['id'] == product_id), None)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(item)

# ── ADMIN PRODUCT ROUTES ──

import uuid
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        price = int(request.form.get('price'))
        category = request.form.get('category')
        emoji = request.form.get('emoji', '🔑')
        badge = request.form.get('badge', '')
        out_of_stock = request.form.get('out_of_stock', 'false') == 'true'

        # Handle multiple images (max 5)
        image_urls = []
        files = request.files.getlist('images')
        for file in files[:5]:  # Limit to 5 images
            if file and file.filename and allowed_file(file.filename):
                url = upload_image(file)
                if url:
                    image_urls.append(url)

        image_url = image_urls[0] if image_urls else None

        bg_colors = {
            'floral': 'linear-gradient(135deg, #FFE4EF, #FFF0F6)',
            'celestial': 'linear-gradient(135deg, #FFF5D6, #FFFAE8)',
            'kawaii': 'linear-gradient(135deg, #E0F0FF, #EAF5FF)',
            'food': 'linear-gradient(135deg, #F0EBFF, #F7F4FF)',
            'bows': 'linear-gradient(135deg, #FFE8D6, #FFF0E8)'
        }

        new_product = {
            'id': str(uuid.uuid4()),
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'emoji': emoji,
            'bg_color': bg_colors.get(category, 'linear-gradient(135deg, #FFE4EF, #FFF0F6)'),
            'badge': '⭐ Best' if badge == 'best' else ('New' if badge == 'new' else None),
            'badge_type': badge if badge else None,
            'reviews': 0,
            'image': image_url,
            'images': image_urls,
            'out_of_stock': out_of_stock
        }

        product_id = add_product_to_db(new_product)
        new_product['id'] = product_id
        return jsonify({'success': True, 'product': new_product})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/delete-product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    delete_product_from_db(product_id)
    return jsonify({'success': True})

@app.route('/admin/toggle-stock/<product_id>', methods=['POST'])
def toggle_stock(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        current_status = product.get('out_of_stock', False)
        new_status = not current_status
        update_product_in_db(product_id, {'out_of_stock': new_status})
        return jsonify({'success': True, 'out_of_stock': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── PAYMENT ROUTES ──

@app.route('/api/create-order', methods=['POST'])
def create_order():
    try:
        from datetime import datetime
        data = request.get_json()
        amount = data.get('amount', 0)  # Total including shipping
        utr = data.get('utr', '')

        # Save order to Firestore with pending_verification status
        order_data = {
            'amount': amount,
            'subtotal': data.get('subtotal', amount),
            'shipping': data.get('shipping', 0),
            'utr': utr,
            'status': 'pending_verification',
            'customer_name': data.get('name', ''),
            'customer_email': data.get('email', ''),
            'customer_phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'pincode': data.get('pincode', ''),
            'cart': data.get('cart', []),
            'created_at': datetime.utcnow().isoformat()
        }
        saved_order_id = save_order(order_data)

        return jsonify({
            'success': True,
            'order_id': saved_order_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/verify-payment/<order_id>', methods=['POST'])
def admin_verify_payment(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        from database import db as firestore_db
        firestore_db.collection('orders').document(order_id).update({
            'status': 'paid'
        })
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
# ── RUN ──

if __name__ == '__main__':
    app.run(debug=True)