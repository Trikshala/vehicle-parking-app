from vehicle import app, db
from flask import render_template, flash, redirect, url_for, abort, request
from functools import wraps
from datetime import datetime, timedelta
from vehicle.controllers.forms import RegistrationForm, LoginForm, CreateParkingLotForm, DeleteParkingLotForm, SearchParkingLot, BookingForm, ReleaseSpotForm, EditProfileForm, AdminSearchForm
from vehicle.models import User, ParkingLot, ParkingSpot, Reservation
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload
from collections import defaultdict

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
        phone_num = form.contact_number.data
        if User.query.filter_by(contact_number = phone_num).first():
            flash(f'Phone number already registered!','danger')
            return redirect(url_for('register_page'))
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


@app.route('/admin/home', methods=["GET", "POST"])
@login_required
@admin_required
def admin_home():
    lots = ParkingLot.query.options(joinedload(ParkingLot.parking_spots)).all()

    for lot in lots:
        lot.parking_spots = [spot for spot in lot.parking_spots if spot.spot_index < lot.max_spots]
        lot.occupied = sum(1 for spot in lot.parking_spots if spot.status == 'O')

    reservations = Reservation.query.all()

    form = CreateParkingLotForm()
    delete_form = DeleteParkingLotForm()
    edit_form = {lot.lot_id: CreateParkingLotForm(obj=lot) for lot in lots}

    if request.method == "POST" and form.validate_on_submit():
        new_lot = ParkingLot(primary_location=form.primary_location.data,full_address=form.full_address.data,pincode=form.pincode.data,cost_per_unit=float(form.cost_per_unit.data),max_spots=form.max_spots.data)
        db.session.add(new_lot)
        db.session.flush()

        existing_spots = ParkingSpot.query.filter_by(lot_id=new_lot.lot_id).count()

        if existing_spots > 0:
            db.session.rollback()
            flash("Something went wrong: This new lot already had spots. Cancelling operation.", "danger")
            return redirect(url_for('admin_home'))

        for i in range(new_lot.max_spots):
            db.session.add(ParkingSpot(status='A', lot_id=new_lot.lot_id, spot_index=i))

        db.session.commit()
        flash('Parking Lot Creation Successful!', category='success')
        return redirect(url_for('admin_home'))

    if form.errors:
        for field_errors in form.errors.values():
            for error_message in field_errors:
                flash(f'There was an error creating the lot: {error_message}', category='danger')

    return render_template('admin_dashboard/admin_home.html',user=current_user,form=form,lots=lots,delete_form=delete_form,edit_form=edit_form,reservations=reservations)


@app.route('/admin/delete_lot/<int:lot_id>', methods=["POST"])
@login_required
@admin_required
def delete_lot(lot_id):
    lot_to_delete = ParkingLot.query.get_or_404(lot_id)

    for spot in lot_to_delete.parking_spots:
        if spot.status == 'O':
            flash("Cannot delete the lot. One or more spots are currently occupied.", "danger")
            return redirect(url_for('admin_home'))

    for spot in lot_to_delete.parking_spots:
        for res in spot.reservations:
            res.archived_primary_location = lot_to_delete.primary_location
            res.archived_spot_id = spot.spot_id
            res.archived_lot_id = lot_to_delete.lot_id

    db.session.commit()
    db.session.delete(lot_to_delete)
    db.session.commit()

    flash("Parking lot deleted successfully.", "success")
    return redirect(url_for('admin_home'))


@app.route('/admin/edit_lot/<int:lot_id>', methods=["POST"])
@login_required
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    form = CreateParkingLotForm(original_id=lot_id, obj=lot)

    if form.validate_on_submit():
        new_max_spots = form.max_spots.data
        new_cost = form.cost_per_unit.data

        if new_max_spots is None or new_cost is None:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('admin_home'))

        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.lot_id, status='O').count() or 0

        if new_max_spots < occupied_spots:
            flash(f"Cannot reduce max spots to {new_max_spots} as {occupied_spots} spot(s) are occupied.", "danger")
            return redirect(url_for('admin_home'))

        if occupied_spots > 0 and float(new_cost) != float(lot.cost_per_unit):
            flash("Cannot change the cost while spots are occupied.", "warning")
            return redirect(url_for('admin_home'))

        old_max_spots = lot.max_spots
        lot.max_spots = new_max_spots
        lot.cost_per_unit = float(new_cost)
        lot.primary_location = form.primary_location.data
        lot.full_address = form.full_address.data
        lot.pincode = form.pincode.data

        if new_max_spots > old_max_spots:
            existing_indexes = {s.spot_index for s in lot.parking_spots}
            for index in range(old_max_spots, new_max_spots):
                if index not in existing_indexes:
                    new_spot = ParkingSpot(status='A', lot_id=lot.lot_id, spot_index=index)
                    db.session.add(new_spot)

        elif new_max_spots < old_max_spots:
            deletable_spots = ParkingSpot.query.filter_by(lot_id=lot.lot_id, status='A')\
                .order_by(ParkingSpot.spot_index.desc()).all()

            to_delete = deletable_spots[:old_max_spots - new_max_spots]

            for spot in to_delete:
                if spot.status != 'A':  
                    flash(f"Cannot delete Spot {spot.spot_index} as it is occupied.", "danger")
                    return redirect(url_for('admin_home'))
                for res in spot.reservations:
                    res.archived_spot_id = spot.spot_id
                    res.archived_lot_id = lot.lot_id
                    res.archived_primary_location = lot.primary_location
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

@app.route('/admin/user_history/<int:user_id>')
@login_required
@admin_required
def user_parking_history(user_id):
    user = User.query.get_or_404(user_id)
    reservations = Reservation.query.filter_by(user_id = user_id).order_by(Reservation.checkin_time.desc()).all()
    return render_template('admin_dashboard/user_parking_history.html', user = user, reservations = reservations)

@app.route('/admin/edit_profile', methods=["GET", "POST"])
@admin_required
@login_required
def edit_admin_profile():
    form = EditProfileForm(obj=current_user)

    if request.method == "POST" and form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email_address = form.email_address.data
        current_user.contact_number = form.contact_number.data
        current_user.address = form.address.data
        current_user.pincode = form.pincode.data
        db.session.commit()
        flash(f"Profile updated Successfully!", "success")
        return redirect(url_for('admin_home'))
    
    elif request.method == "GET":
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email_address.data = current_user.email_address
        form.contact_number.data = current_user.contact_number
        form.address.data = current_user.address
        form.pincode.data = current_user.pincode
    

    return render_template('admin_dashboard/admin_edit.html', form = form)

@app.route('/admin/search', methods= ["GET", "POST"])
@login_required
@admin_required
def admin_search():
    form = AdminSearchForm()
    edit_form = {}
    delete_form = {}
    user_record = None
    lots = None
    reservations = []
    search_choice = None
    search_string = None
    if form.validate_on_submit():
        search_choice = form.search_choice.data
        search_string = form.search_string.data.strip()
        if search_choice == 'u_id':
            try:
                search_string = int(search_string)
            except ValueError:
                flash('User id must be an integer', 'danger')
            user_record = User.query.filter_by(id = search_string).first()
            if not user_record:
                flash('User does not exist.', 'danger')
        elif search_choice == 'loc':
            lots = ParkingLot.query.filter_by(primary_location = search_string).all()
            for lot in lots:
                lot.occupied = sum(1 for spot in lot.parking_spots if spot.status == 'O')
            if not lots:
                flash('Location not found. Try checking the spelling', 'danger')
            reservations = Reservation.query.all()
            delete_form = DeleteParkingLotForm()
            edit_form = {}
            for lot in lots:
                edit_form[lot.lot_id] = CreateParkingLotForm(obj=lot)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", "danger")
    return render_template('admin_dashboard/admin_search.html', form = form, search_choice = search_choice, user_record = user_record, lots = lots, search_string = search_string, reservations = reservations, edit_form = edit_form, delete_form = delete_form)

@app.route('/admin/summary')
@login_required
@admin_required
def admin_summary():

    # Revenue Generated Bar Graph Data
    reservations = Reservation.query.all()
    revenue_data = {}

    for res in reservations:
        if res.final_cost is None:
            continue
        if res.spot and res.spot.lot:
            lot_id = res.spot.lot.lot_id
            label = f"{res.spot.lot.primary_location} (ID: {lot_id})"
        else:
            lot_id = res.archived_lot_id or -1
            label = f"{res.archived_primary_location or 'Deleted Lot'} (ID: {res.archived_lot_id}) (Deleted)"

        if lot_id not in revenue_data:
            revenue_data[lot_id] = {
                "label": label,
                "value": 0
            }

        revenue_data[lot_id]["value"] += res.final_cost or 0

    chart_data = {
        "labels": [v["label"] for v in revenue_data.values()],
        "values": [round(v["value"], 2) for v in revenue_data.values()]
    }

    # Occupied/Available Spot distribution Bar Graph Data
    reservation_dist = {}
    lots = ParkingLot.query.all()
    for lot in lots:
        occupied_count = 0
        total = lot.max_spots
        for spot in lot.parking_spots:
            if spot.status == 'O':
                occupied_count += 1
        reservation_dist[lot.lot_id] = {'label': f"{lot.primary_location} (ID:{lot.lot_id})", 'available': total - occupied_count,
            'occupied': occupied_count}

    second_chart = {
        "labels": [v['label'] for v in reservation_dist.values()],
        "available": [v['available'] for v in reservation_dist.values()],
        "occupied": [v['occupied'] for v in reservation_dist.values()]
    }

    return render_template('admin_dashboard/admin_summary.html',chart_data=chart_data, second_chart=second_chart)



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
            lot_info.append({'lot_id': lot.lot_id, 'full_address': lot.full_address, 'cost_per_unit': lot.cost_per_unit, 'available_count': len(available_spots), 'spot_id': spot.spot_id if spot else None})
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

        existing_vehicle = Reservation.query.filter_by(nameplate_num=vehicle_number, actual_checkout_time=None).first()
        if existing_vehicle:
            flash("This vehicle is already actively parked!", "danger")
            return redirect(url_for("user_home"))

        spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').order_by(ParkingSpot.spot_index).first()
        if not spot:
            flash('All the spots in this lot are full!', 'danger')
            return redirect(url_for("user_home"))

        existing_res = Reservation.query.filter_by(spot_id=spot.spot_id).order_by(Reservation.checkin_time.desc()).first()
        if existing_res and existing_res.actual_checkout_time is None:
            flash("This parking spot already has an active reservation.", "danger")
            return redirect(url_for("user_home"))


        checkin_time = datetime.now()
        checkout_time = checkin_time + timedelta(hours=num_hrs)
        estimated_cost = cost_per_hour * num_hrs

        reservation = Reservation(spot_id=spot.spot_id, user_id=user_id, checkin_time=checkin_time, checkout_time=checkout_time, vehicle_model=vehicle_model, nameplate_num=vehicle_number, cost_per_unit=cost_per_hour, estimated_cost=estimated_cost)

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
    reservation.final_cost = reservation.calculate_cost_at(reservation.actual_checkout_time)
    reservation.spot.status = "A"
    db.session.commit()

    flash(f"Spot Released Successfully! Total Cost : {reservation.total_cost}", "success")

    return redirect(url_for('user_home'))

@app.route('/user/edit_profile', methods=["GET", "POST"])
@user_required
@login_required
def edit_user_profile():
    form = EditProfileForm(obj=current_user)

    if request.method == "POST" and form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email_address = form.email_address.data
        current_user.contact_number = form.contact_number.data
        current_user.address = form.address.data
        current_user.pincode = form.pincode.data
        db.session.commit()
        flash(f"Profile updated Successfully!", "success")
        return redirect(url_for('user_home'))
    
    elif request.method == "GET":
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email_address.data = current_user.email_address
        form.contact_number.data = current_user.contact_number
        form.address.data = current_user.address
        form.pincode.data = current_user.pincode
    
    return render_template('user_dashboard/user_edit.html', form = form)

@app.route('/user/summary')
@login_required
@user_required
def user_summary():
    reservations = Reservation.query.all()
    res_freq = {}

    for res in reservations:
        if res.user_id != current_user.id:
            continue
        if res.spot and res.spot.lot:
            lot_id = res.spot.lot.lot_id  
            label = f"{res.spot.lot.primary_location} (ID: {lot_id})"
        else:
            lot_id = res.archived_lot_id if res.archived_lot_id is not None else -1
            label = f"{res.archived_primary_location or "Deleted lot"}" + " (Deleted) " + "(ID: {lot_id})"
        if lot_id in res_freq:
                res_freq[lot_id]['frequency'] += 1
        else:
            res_freq[lot_id] = {
                'label': label,
                'frequency': 1
            }

    user_res = {
        "lots" : [v['label'] for v in res_freq.values()],
        "visits" : [v['frequency'] for v in res_freq.values()]
    }

    duration_data = defaultdict(list)
    for res in reservations:
        if res.user_id != current_user.id:
            continue
        if res.spot and res.spot.lot:
            lot_id = res.spot.lot.lot_id
            lot_label = f"{res.spot.lot.primary_location} (ID: {lot_id})"
        else:
            lot_id = res.archived_lot_id if res.archived_lot_id is not None else -1
            lot_label = (res.archived_primary_location or "Deleted Lot") + " (Deleted)"
        start = res.checkin_time
        end = res.actual_checkout_time or datetime.now()
        duration = (end - start).total_seconds()/60
        
        duration_data[lot_id].append((lot_label, duration))

    avg_dur_data = {
        'labels' : [],
        'values' : []
    }

    for id, values in duration_data.items():
        labels, durations = zip(*values)
        avg = sum(durations) / len(durations)
        avg_dur_data['labels'].append(labels[0])
        avg_dur_data['values'].append(round(avg, 2))

    return render_template('user_dashboard/user_summary.html', user_res = user_res, avg_dur_data = avg_dur_data)

# Logout Route
@app.route('/logout')
def logout_page():
    logout_user()
    flash(f'You have been logged out.', category='info')
    return render_template('welcome.html')


