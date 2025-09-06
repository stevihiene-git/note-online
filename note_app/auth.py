# auth.py (updated)
from flask import Blueprint, render_template, redirect, url_for, flash, request
from datetime import datetime
# from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import generate_password_hash, check_password_hash  # Add these imports
from note_app import db
from note_app.models import User
from note_app.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, current_user
from sqlalchemy.exc import OperationalError, IntegrityError
from note_app.email import send_welcome_email
from note_app.models import User

auth2 = Blueprint('auth', __name__,template_folder='public')

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@auth2.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('views.home'))
            else:
                flash('Login unsuccessful. Please check email and password.', 'danger')
        except OperationalError as e:
            logger.error(f"Database connection error: {e}")
            flash('Database connection error. Please try again later.', 'danger')
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            flash('An unexpected error occurred. Please try again.', 'danger')
    
    return render_template("login.html", title="Login", form=form)

@auth2.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    
    form = RegistrationForm()
    # if form.validate_on_submit():
    #     hashed_password = generate_password_hash(form.password.data)
    #     user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
    #     db.session.add(user)
    #     db.session.commit()
    #     # Send welcome email
    #     send_welcome_email(user)
    #     flash('Your account has been created! You can now log in.', 'success')
    #     return redirect(url_for('auth.login'))
    
    # date = datetime.now()
    # current_date = date.strftime("%Y")
    # return render_template("signup.html", title="Sign Up", form=form, current_date=current_date)
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered. Please use a different email or login.', 'danger')
                return render_template("signup.html", title="Sign Up", form=form)
            
            # Check if username already exists
            existing_username = User.query.filter_by(username=form.username.data).first()
            if existing_username:
                flash('Username already taken. Please choose a different username.', 'danger')
                return render_template("signup.html", title="Sign Up", form=form)
            
            # Create new user
            hashed_password = generate_password_hash(form.password.data)
            user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            
            # Send welcome email - ADD THIS LINE
            send_welcome_email(user)
            
            flash('Your account has been created! Welcome email sent.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template("signup.html", title="Sign Up", form=form)


@auth2.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('views.home'))