from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(150))
    medicine_name = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    date = db.Column(db.String(50))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(150))
    medicine_name = db.Column(db.String(150))
    quantity = db.Column(db.Integer)
    date = db.Column(db.String(50))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful. Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    medicines = Medicine.query.all()
    total_quantity = sum(med.quantity for med in medicines)
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_purchases = Purchase.query.filter(Purchase.date == today).count()
    today_sales = Sale.query.filter(Sale.date == today).count()
    
    return render_template('dashboard.html', 
                         medicines=medicines,
                         total_quantity=total_quantity,
                         today_purchases=today_purchases,
                         today_sales=today_sales)

@app.route('/stock', methods=['GET', 'POST'])
def stock():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        existing = Medicine.query.filter_by(name=name).first()
        if existing:
            existing.quantity += quantity
            existing.price = price
        else:
            med = Medicine(name=name, quantity=quantity, price=price)
            db.session.add(med)
        db.session.commit()
        flash('Stock updated!')
    medicines = Medicine.query.all()
    return render_template('stock.html', medicines=medicines)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        supplier = request.form['supplier']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        date = datetime.now().strftime('%Y-%m-%d')
        purchase = Purchase(supplier_name=supplier, medicine_name=product, quantity=quantity, price=price, date=date)
        db.session.add(purchase)
        med = Medicine.query.filter_by(name=product).first()
        if med:
            med.quantity += quantity
        else:
            db.session.add(Medicine(name=product, quantity=quantity, price=price))
        db.session.commit()
        flash('Purchase recorded!')
    return render_template('purchase.html')

@app.route('/sale', methods=['GET', 'POST'])
def sale():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        customer = request.form['customer']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        med = Medicine.query.filter_by(name=product).first()
        if med and med.quantity >= quantity:
            med.quantity -= quantity
            date = datetime.now().strftime('%Y-%m-%d')
            sale = Sale(customer_name=customer, medicine_name=product, quantity=quantity, date=date)
            db.session.add(sale)
            db.session.commit()
            flash('Sale recorded!')
        else:
            flash('Insufficient stock or medicine not found')
    return render_template('sale.html')

@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    sales = Sale.query.all()
    purchases = Purchase.query.all()
    return render_template('reports.html', sales=sales, purchases=purchases)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)