from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'vigneshwaran_2025_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# ==================== MODELS ======================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier = db.Column(db.String(100))
    product = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    discount = db.Column(db.Float)
    date = db.Column(db.String(50))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String(100))
    doctor = db.Column(db.String(100))
    product = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    discount = db.Column(db.Float)
    tax = db.Column(db.Float)
    is_returned = db.Column(db.String(10))
    date = db.Column(db.String(50))

# ==================== ROUTES ======================

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            session['user'] = uname
            return redirect(url_for('dashboard'))
        flash("Invalid username or password")
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if User.query.filter_by(username=uname).first():
            flash("Username already exists")
        else:
            db.session.add(User(username=uname, password=pwd))
            db.session.commit()
            flash(f"Signed up as {uname}. You can now login.")
            return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("dashboard.html")

@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        qty = int(request.form['quantity'])
        price = float(request.form['price'])
        existing = Medicine.query.filter_by(name=name).first()
        if existing:
            existing.quantity += qty
            existing.price = price
        else:
            db.session.add(Medicine(name=name, quantity=qty, price=price))
        db.session.commit()
        flash("Medicine added/updated successfully.")
    meds = Medicine.query.all()
    return render_template("medicine.html", medicines=meds)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    if 'user' not in session:
        return redirect(url_for('login'))
    meds = Medicine.query.all()
    if request.method == 'POST':
        supplier = request.form['supplier']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        discount = float(request.form['discount'])
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        db.session.add(Purchase(supplier=supplier, product=product, quantity=quantity, price=price, discount=discount, date=date))
        # update stock
        med = Medicine.query.filter_by(name=product).first()
        if med:
            med.quantity += quantity
        db.session.commit()
        flash("Purchase recorded.")
    return render_template("purchase.html", medicines=meds)

@app.route('/sale', methods=['GET', 'POST'])
def sale():
    if 'user' not in session:
        return redirect(url_for('login'))
    meds = Medicine.query.all()
    if request.method == 'POST':
        customer = request.form['customer']
        doctor = request.form['doctor']
        product = request.form['product']
        quantity = int(request.form['quantity'])
        discount = float(request.form['discount'])
        tax = float(request.form['tax'])
        is_returned = request.form['is_returned']
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        med = Medicine.query.filter_by(name=product).first()
        if med and med.quantity >= quantity:
            med.quantity -= quantity
            db.session.add(Sale(
                customer=customer,
                doctor=doctor,
                product=product,
                quantity=quantity,
                discount=discount,
                tax=tax,
                is_returned=is_returned,
                date=date
            ))
            db.session.commit()
            flash("Sale recorded.")
            return render_template("receipt.html", sale={
                "customer": customer, "doctor": doctor, "product": product,
                "quantity": quantity, "discount": discount, "tax": tax,
                "is_returned": is_returned, "date": date
            })
        else:
            flash("Insufficient stock or product not found.")
    return render_template("sale.html", medicines=meds)

# ==================== MAIN ======================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
