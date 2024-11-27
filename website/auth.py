from flask import Blueprint, flash, render_template, request, url_for, redirect
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db

#Define the auth blueprint
auth_bp = Blueprint('auth', __name__)

#Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    error = None
    
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        user = db.session.scalar(db.select(User).where(User.email == email))
        
        if user is None:
            error = 'Incorrect Email'
        elif not check_password_hash(user.password_hash, password):
            error = 'Incorrect password'
        
        if error is None:
            login_user(user)
            nextp = request.args.get('next')
            if nextp is None or not nextp.startswith('/'):
                return redirect(url_for('main.index'))
            return redirect(nextp)
        else:
            flash(error)
    return render_template('login.html', login_form=login_form)

#Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    error = None
    
    if register_form.validate_on_submit():
        first_name = register_form.first_name.data
        surname = register_form.surname.data
        email = register_form.email.data
        password = register_form.password.data
        contact_number = register_form.contact_number.data
        street_address = register_form.street_address.data
        is_admin = False
        
        #Check if user exists
        existing_user = db.session.scalar(db.select(User).where(User.email == email))
        if existing_user:
            error = 'User Already Exists'
        
        if error is None:
            try:
                password_hash = generate_password_hash(password).decode('utf-8')
                new_user = User(
                    first_name=first_name, 
                    surname=surname, 
                    email=email, 
                    password_hash=password_hash, 
                    contact_number=contact_number, 
                    street_address=street_address,
                    is_admin=is_admin
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Registration successful! You are now logged in.', 'success')
                return redirect(url_for('main.index'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'error')
        else:
            flash(error)
            
    return render_template('register.html', register_form=register_form)

#Logout route
@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.')
    return redirect(url_for('main.index'))
