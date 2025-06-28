from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pharmacy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Custom template filters
@app.template_filter('currency')
def currency_filter(amount):
    """Format a number as currency"""
    if amount is None:
        return "₹0.00"
    return f"₹{amount:,.2f}"

@app.template_filter('time_ago')
def time_ago_filter(date_str):
    """Convert a date string to relative time"""
    try:
        date_obj = datetime.strptime(date_str, '%d-%m-%Y %H:%M')
        delta = datetime.now() - date_obj
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    except:
        return date_str

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff')

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(50))
    expiry = db.Column(db.String(10))
    quantity = db.Column(db.Integer, default=0)
    mrp = db.Column(db.Float)
    rate = db.Column(db.Float)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_no = db.Column(db.String(20))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    date = db.Column(db.String(20))
    discount = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float)
    is_return = db.Column(db.Boolean, default=False)

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.String(100))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    batch = db.Column(db.String(50))
    expiry = db.Column(db.String(10))
    quantity = db.Column(db.Integer)
    rate = db.Column(db.Float)
    date = db.Column(db.String(20))

# Initialize database
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        if not User.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123')
            admin = User(username='admin', password=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()

# Call the initialization function
init_db()

# ... rest of your routes and application code ...

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not username or not password:
            flash('Username and password are required', 'danger')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('signup'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main Application Routes
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    medicines = Medicine.query.count()
    customers = Customer.query.count()
    sales = Sale.query.count()
    
    today = datetime.now().strftime('%d-%m-%Y')
    today_purchases = Purchase.query.filter_by(date=today).count()
    today_sales = Sale.query.filter_by(date=today).count()
    
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
    low_stock = Medicine.query.filter(Medicine.quantity < 10).all()
    
    return render_template('dashboard.html',
                         medicines=medicines,
                         customers=customers,
                         sales=sales,
                         today_purchases=today_purchases,
                         today_sales=today_sales,
                         recent_sales=recent_sales,
                         low_stock=low_stock)

# Medicine Routes
@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        batch = request.form['batch']
        expiry = request.form['expiry']
        quantity = int(request.form['quantity'])
        mrp = float(request.form['mrp'])
        rate = float(request.form['rate'])
        
        med = Medicine(name=name, batch=batch, expiry=expiry,
                      quantity=quantity, mrp=mrp, rate=rate)
        db.session.add(med)
        db.session.commit()
        flash('Medicine added successfully', 'success')
        return redirect(url_for('medicine'))
    
    medicines = Medicine.query.all()
    return render_template('medicine.html', medicines=medicines)

# Purchase Routes
@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    medicines = Medicine.query.all()
    
    if request.method == 'POST':
        supplier = request.form['supplier']
        medicine_id = int(request.form['medicine'])
        batch = request.form['batch']
        expiry = request.form['expiry']
        quantity = int(request.form['quantity'])
        rate = float(request.form['rate'])
        
        purchase = Purchase(supplier=supplier, medicine_id=medicine_id,
                          batch=batch, expiry=expiry, quantity=quantity,
                          rate=rate, date=datetime.now().strftime('%d-%m-%Y'))
        db.session.add(purchase)
        
        med = Medicine.query.get(medicine_id)
        if med:
            med.quantity += quantity
        else:
            flash('Medicine not found', 'danger')
            return redirect(url_for('purchase'))
        
        db.session.commit()
        flash('Purchase recorded successfully', 'success')
        return redirect(url_for('purchase'))
    
    return render_template('purchase.html', medicines=medicines)

# Sale Routes
@app.route('/sale', methods=['GET', 'POST'])
def sale():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    medicines = Medicine.query.all()
    customers = Customer.query.all()
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        customer_id = int(request.form['customer'])
        doctor_id = int(request.form.get('doctor', 0)) or None
        discount = float(request.form.get('discount', 0))
        tax = float(request.form.get('tax', 0))
        
        sale = Sale(
            bill_no=f"BIL{datetime.now().strftime('%Y%m%d%H%M')}",
            customer_id=customer_id,
            doctor_id=doctor_id,
            date=datetime.now().strftime('%d-%m-%Y %H:%M'),
            discount=discount,
            tax=tax,
            total=0,
            is_return=False
        )
        db.session.add(sale)
        db.session.flush()
        
        total = 0
        medicine_ids = request.form.getlist('medicine_id')
        quantities = request.form.getlist('quantity')
        
        for med_id, qty in zip(medicine_ids, quantities):
            if not qty or int(qty) <= 0:
                continue
                
            medicine = Medicine.query.get(int(med_id))
            if not medicine or medicine.quantity < int(qty):
                db.session.rollback()
                flash(f'Insufficient stock for {medicine.name}', 'danger')
                return redirect(url_for('sale'))
                
            sale_item = SaleItem(
                sale_id=sale.id,
                medicine_id=medicine.id,
                quantity=int(qty),
                price=medicine.mrp
            )
            db.session.add(sale_item)
            
            medicine.quantity -= int(qty)
            total += medicine.mrp * int(qty)
        
        if total == 0:
            db.session.rollback()
            flash('No items selected for sale', 'danger')
            return redirect(url_for('sale'))
        
        sale.total = total - (total * discount / 100) + (total * tax / 100)
        db.session.commit()
        
        flash('Sale recorded successfully', 'success')
        return redirect(url_for('receipt', sale_id=sale.id))
    
    return render_template('sale.html', 
                         medicines=medicines,
                         customers=customers,
                         doctors=doctors)

@app.route('/sales')
def sales():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('sales.html', sales=sales)

@app.route('/sale/return/<int:sale_id>', methods=['GET', 'POST'])
def sale_return(sale_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    original_sale = Sale.query.get_or_404(sale_id)
    
    if request.method == 'POST':
        return_sale = Sale(
            bill_no=f"RET{datetime.now().strftime('%Y%m%d%H%M')}",
            customer_id=original_sale.customer_id,
            doctor_id=original_sale.doctor_id,
            date=datetime.now().strftime('%d-%m-%Y %H:%M'),
            discount=0,
            tax=0,
            total=original_sale.total,
            is_return=True
        )
        db.session.add(return_sale)
        db.session.flush()
        
        original_items = SaleItem.query.filter_by(sale_id=original_sale.id).all()
        for item in original_items:
            medicine = Medicine.query.get(item.medicine_id)
            if medicine:
                medicine.quantity += item.quantity
            
            return_item = SaleItem(
                sale_id=return_sale.id,
                medicine_id=item.medicine_id,
                quantity=item.quantity,
                price=item.price
            )
            db.session.add(return_item)
        
        db.session.commit()
        flash('Return processed successfully', 'success')
        return redirect(url_for('receipt', sale_id=return_sale.id))
    
    return render_template('sales_return.html', sale=original_sale)

@app.route('/receipt/<int:sale_id>')
def receipt(sale_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    sale = Sale.query.get_or_404(sale_id)
    items = SaleItem.query.filter_by(sale_id=sale_id).all()
    return render_template('receipt.html', sale=sale, items=items)

# Report Routes
@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    sales = Sale.query.order_by(Sale.date.desc()).limit(10).all()
    purchases = Purchase.query.order_by(Purchase.date.desc()).limit(10).all()
    return render_template('reports.html', sales=sales, purchases=purchases)

# Initialize database
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('admin123')
        admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)