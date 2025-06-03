from flask import Flask, render_template, url_for, redirect, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///salon.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(150), default='Unknown')
    birthday = db.Column(db.String(10))  # store as 'YYYY-MM-DD'
    address = db.Column(db.String(250))
    image = db.Column(db.String(250))  # store filename only

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form.get('name', 'Unknown')
        birthday = request.form.get('birthday', '')
        address = request.form.get('address', '')

        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Choose another.", "danger")
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Handle image upload
        image_file = request.files.get('image')
        image_filename = ''
        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Create new user
        new_user = User(
            username=username,
            password=hashed_password,
            name=name,
            birthday=birthday,
            address=address,
            image=image_filename
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    # Calculate age if birthday is present and valid
    age = None
    birthday = user.birthday
    if birthday and len(birthday) == 10:
        try:
            birth_year = int(birthday.split('-')[0])
            age = datetime.now().year - birth_year
        except Exception:
            age = None

    return render_template('profiledis.html', user=user, age=age)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
