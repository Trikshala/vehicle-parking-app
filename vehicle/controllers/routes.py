from vehicle import app, db
from flask import render_template, flash, redirect, url_for, abort, request
from functools import wraps
from datetime import datetime, timedelta
from vehicle.controllers.forms import RegistrationForm, LoginForm, CreateParkingLotForm, DeleteParkingLotForm, SearchParkingLot, BookingForm, ReleaseSpotForm
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
        return redirect(url_for('user_home'))
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
    lots = ParkingLot.query.options(joinedload(ParkingLot.parking_spots.and_(ParkingSpot.spot_id))).all()
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
        for index in range(new_lot.max_spots):
            new_spot = ParkingSpot(status = 'A',lot_id=new_lot.lot_id, spot_index=index)
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

@app.route('/user/home', methods=["GET", "POST"])
@login_required
@user_required
def user_home():
    form = SearchParkingLot()
    release_form = ReleaseSpotForm()
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    areas = db.session.query(ParkingLot.primary_location).distinct().all()
    form.location.choices = [(area[0], area[0]) for area in areas]

    available_lots = None
    lot_info = []  

    if form.validate_on_submit():
        selected_area = form.location.data
        available_lots = ParkingLot.query.filter_by(primary_location=selected_area).all()

        for lot in available_lots:
            available_spots = [s for s in lot.parking_spots if s.status == 'A']
            spot = sorted(available_spots, key=lambda s: s.spot_id)[0] if available_spots else None
            lot_info.append({
                'lot_id': lot.lot_id,
                'full_address': lot.full_address,
                'cost_per_unit': lot.cost_per_unit,
                'available_count': len(available_spots),
                'spot_id': spot.spot_id if spot else None
            })
    return render_template('user_dashboard/user_home.html', user=current_user, form=form, lots=lot_info, reservations = reservations, now=datetime.now(), datetime=datetime, release_form = release_form)


@app.route('/user/book_spot', methods=["POST"])
@login_required
@user_required
def book_spot():
    form = BookingForm()
    if form.validate_on_submit():
        lot_id = form.lot_id.data
        user_id = current_user.id
        vehicle_model = form.vehicle_model.data
        vehicle_number = form.vehicle_number.data
        num_hrs = int(form.no_of_hours.data)
        cost_per_hour = float(form.cost_per_hour.data)
        existing_vehicle = Reservation.query.filter_by(nameplate_num=vehicle_number).first()
        if existing_vehicle:
            flash("This vehicle is already booked!", "danger")
            return redirect(url_for("user_home"))

        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').order_by(ParkingSpot.spot_index).first()
        if not spot:
            flash('All the spots in this lot are full!', 'danger')
            return redirect(url_for("user_home"))

        existing_res = Reservation.query.filter_by(spot_id=spot.spot_id).order_by(Reservation.checkin_time.desc()).first()
        if existing_res and existing_res.checkout_time > datetime.now():
            flash("This parking spot already has an active reservation.", "danger")
            return redirect(url_for("user_home"))

        checkin_time = datetime.now()
        checkout_time = checkin_time + timedelta(hours=num_hrs)
        estimated_cost = cost_per_hour * num_hrs

        reservation = Reservation(
            spot_id=spot.spot_id,
            user_id=user_id,
            checkin_time=checkin_time,
            checkout_time=checkout_time,
            vehicle_model=vehicle_model,
            nameplate_num=vehicle_number,
            cost_per_unit=cost_per_hour,
            estimated_cost=estimated_cost
        )

        spot.status = 'O'
        db.session.add(reservation)
        db.session.commit()

        flash(f'Spot reservation successful! Spot ID: {spot.spot_id}, Estimated Cost: ₹{estimated_cost}', 'success')
        return redirect(url_for('user_home')) 

    flash('Something went wrong! Reservation unsuccessful!', 'danger')
    return redirect(url_for('user_home'))

@app.route('/user/release_spot/<int:r_id>', methods = ["POST"])
@login_required
@user_required
def release_spot(r_id):
    reservation = Reservation.query.get_or_404(r_id)
    if reservation.actual_checkout_time or reservation.spot.status == "A":
        flash("Spot already released!", "danger")
        return redirect(url_for('user_home'))
    reservation.actual_checkout_time = datetime.now()
    reservation.spot.status = "A"
    db.session.commit()

    flash(f"Spot Released Successfully! Total Cost : {reservation.total_cost}", "success")

    return redirect(url_for('user_home'))


@app.route('/logout')
def logout_page():
    logout_user()
    flash(f'You have been logged out.', category='info')
    return render_template('welcome.html')

