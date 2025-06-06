from vehicle import app, db
from flask import render_template, flash, redirect, url_for, abort
from functools import wraps
from vehicle.controllers.forms import RegistrationForm, LoginForm
from vehicle.models import User
from flask_login import login_user, logout_user, login_required, current_user

@app.route('/')
@app.route('/home')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username = form.username.data).first()
        if attempted_user:
            if attempted_user.check_password(password_to_check = form.pass_1.data):
                login_user(attempted_user)
                if attempted_user.is_admin:
                    flash(f'Welcome! You are now logged in as {form.username.data}', category='success')
                    return redirect(url_for('admin_home'))
                else:
                    flash(f'Welcome! You are now logged in as {form.username.data}', category='success')
                    return redirect(url_for('user_home'))
            else:
                flash(f'Username and password do not match. Please recheck.', category='danger')
        else:
            flash(f'Sorry! Username does not exist. Please recheck.', category='danger')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username = form.username.data, email_address = form.email_address.data, contact_number = form.contact_number.data, address = form.address.data)
        new_user.password = form.pass_1.data
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash(f'Account Creation Successful! You are now logged in as : {new_user.username}', category='success')
        return redirect(url_for('welcome'))
    if form.errors != {} :
        for field_errors in form.errors.values():
            for error_message in field_errors:
                flash(f'There was an error creating your account: {error_message}', category='danger')
    return render_template('auth/register.html', form=form)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_page'))
        if not current_user.is_admin:
            flash(f'You do not have permission to access this page!',category='danger')
            return redirect(url_for('user_home'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_page'))
        if current_user.is_admin:
            flash(f'You do not have permission to access this page!',category='danger')
            return redirect(url_for('admin_home'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/home')
@login_required
@admin_required
def admin_home():
    return render_template('admin_dashboard/admin_home.html', user = current_user)

@app.route('/user/home')
@login_required
@user_required
def user_home():
    return render_template('user_dashboard/user_home.html', user = current_user)

@app.route('/logout')
def logout_page():
    logout_user()
    flash(f'You have been logged out.', category='info')
    return render_template('welcome.html')

