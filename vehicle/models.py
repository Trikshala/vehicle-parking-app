from . import db
from datetime import datetime

class User(db.Model):
    user_id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(length=20), nullable = False, unique = True)
    password = db.Column(db.String(length=30), nullable = False)
    email_address =  db.Column(db.String(length=40), nullable = False, unique = True)
    conatct_number = db.Column(db.String(10), nullable= True, unique = True)
    address = db.Column(db.String(length=50), nullable = False)
    is_admin = db.Column(db.Boolean(), default = 0)
    reservations = db.relationship('Reservation', backref = 'user', lazy = True)

class ParkingLot(db.Model):
    lot_id = db.Column(db.Integer(), primary_key = True)
    primary_location = db.Column(db.String(length=20), nullable = False, unique = True)
    full_address = db.Column(db.String(length=50), nullable = False)
    pincode = db.Column(db.String(6), nullable = False)
    max_spots = db.Column(db.Integer(), nullable = False)
    cost_per_unit = db.Column(db.Integer(), nullable = False)
    parking_spots = db.relationship('ParkingSpot', backref = 'lot', lazy = True)

class ParkingSpot(db.Model):
    spot_id = db.Column(db.Integer(), primary_key = True)
    status = db.Column(db.String(1), default = 'A')
    lot_id = db.Column(db.Integer(), db.ForeignKey('parking_lot.lot_id'))
    reservations = db.relationship('Reservation', backref = 'spot', lazy = True)

class Reservation(db.Model):
    r_id = db.Column(db.Integer(), primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
    spot_id = db.Column(db.Integer(), db.ForeignKey('parking_spot.spot_id'))
    checkin_time = db.Column(db.DateTime, default = datetime.utcnow)
    checkout_time = db.Column(db.DateTime, nullable = False)
    vehicle_model = db.Column(db.String(length=20), nullable = False)
    nameplate_num = db.Column(db.String(15), nullable=False, unique = True)
    cost_per_unit = db.Column(db.Float, nullable = False)
    total_cost = db.Column(db.Float, nullable = True)