import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

import firebase_admin
from firebase_admin import credentials, firestore
import json

# Connect to Firebase
firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
if firebase_creds_json:
    cred_dict = json.loads(firebase_creds_json)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate('firebase-key.json')

firebase_admin.initialize_app(cred)

# Get database
db = firestore.client()
def upload_image(file):
    try:
        result = cloudinary.uploader.upload(
            file,
            folder='charmly',
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'fill'},
                {'quality': 'auto'}
            ]
        )
        return result['secure_url']
    except Exception as e:
        print('Image upload error:', e)
        return None

# ── PRODUCTS ──

def get_all_products():
    docs = db.collection('products').stream()
    products = []
    for doc in docs:
        product = doc.to_dict()
        product['id'] = doc.id
        products.append(product)
    return products

def get_product_by_id(product_id):
    doc = db.collection('products').document(product_id).get()
    if doc.exists:
        product = doc.to_dict()
        product['id'] = doc.id
        return product
    return None

def add_product_to_db(product_data):
    doc_ref = db.collection('products').add(product_data)
    return doc_ref[1].id

def delete_product_from_db(product_id):
    db.collection('products').document(product_id).delete()
    return True

def update_product_in_db(product_id, data):
    db.collection('products').document(product_id).update(data)
    return True

# ── ORDERS ──

def save_order(order_data):
    doc_ref = db.collection('orders').add(order_data)
    return doc_ref[1].id

def get_all_orders():
    docs = db.collection('orders').order_by(
        'created_at', direction=firestore.Query.DESCENDING
    ).stream()
    orders = []
    for doc in docs:
        order = doc.to_dict()
        order['id'] = doc.id
        orders.append(order)
    return orders