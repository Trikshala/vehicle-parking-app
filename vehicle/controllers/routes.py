from vehicle import app, db
from flask import render_template, flash, redirect, url_for, abort, request
from functools import wraps
from vehicle.controllers.forms import RegistrationForm, LoginForm, CreateParkingLotForm, DeleteParkingLotForm
from vehicle.models import User, ParkingLot, ParkingSpot, Reservation
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload

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
        new_user = User(first_name = form.first_name.data, last_name = form.last_name.data, email_address = form.email_address.data, username = form.username.data,  contact_number = form.contact_number.data, address = form.address.data, pincode = form.pincode.data)
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


# access permissions

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


# Admin routes

@app.route('/admin/home', methods=["GET","POST"])
@login_required
@admin_required
def admin_home():
    lots = ParkingLot.query.options(joinedload(ParkingLot.parking_spots)).all()
    reservations = Reservation.query.all()
    form = CreateParkingLotForm()
    delete_form = DeleteParkingLotForm()
    edit_form = {}
    for lot in lots:
        edit_form[lot.lot_id] = CreateParkingLotForm(obj = lot)
    if form.validate_on_submit():
        new_lot = ParkingLot(primary_location = form.primary_location.data, full_address = form.full_address.data, pincode= form.pincode.data,cost_per_unit = float(form.cost_per_unit.data), max_spots = form.max_spots.data )
        db.session.add(new_lot)
        db.session.flush()
        for _ in range(new_lot.max_spots):
            new_spot = ParkingSpot(status = 'A', lot_id = new_lot.lot_id)
            db.session.add(new_spot)
        db.session.commit()
        flash(f'Parking Lot Creation Successful! ', category='success')
        return redirect(url_for('admin_home'))
    if form.errors != {} :
        for field_errors in form.errors.values():
            for error_message in field_errors:
                flash(f'There was an error creating the lot: {error_message}', category='danger')
    return render_template('admin_dashboard/admin_home.html', user = current_user, form=form, lots=lots, delete_form = delete_form, edit_form = edit_form, reservations=reservations)

@app.route('/admin/delete_lot/<int:lot_id>', methods = ["POST"])
@login_required
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    ParkingSpot.query.filter_by(lot_id = lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    flash(f"The parking lot has been successfully deleted.", category='success')
    return redirect(url_for('admin_home'))

@app.route('/admin/edit_lot/<int:lot_id>', methods=["POST"])
@login_required
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    form = CreateParkingLotForm(original_id = lot_id, obj = lot)
    if form.validate_on_submit():
        old_max_spots = lot.max_spots
        form.populate_obj(lot)
        if lot.max_spots > old_max_spots:
            for _ in range(lot.max_spots - old_max_spots):
                new_spot = ParkingSpot(status = 'A', lot_id = lot.lot_id)
                db.session.add(new_spot)
        elif lot.max_spots < old_max_spots:
            spots_to_delete = ParkingSpot.query.filter_by(lot_id=lot.lot_id).order_by(ParkingSpot.spot_id.desc()).limit(old_max_spots - lot.max_spots).all()
            for spot in spots_to_delete:
                db.session.delete(spot)
        db.session.commit()
        flash("Parking Lot Updated Successfully!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "danger")

    return redirect(url_for('admin_home'))

@app.route('/admin/users')
@login_required
@admin_required
def display_users():
    users = User.query.filter_by(is_admin= False).all()
    return render_template('admin_dashboard/display_users.html', user = current_user, users = users)






# User routes

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

