from . import db
from datetime import datetime, timedelta
from vehicle import bcrypt
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key = True)
    first_name = db.Column(db.String(50), nullable = False)
    last_name = db.Column(db.String(50), nullable = False)
    email_address =  db.Column(db.String(length=60), nullable = False, unique = True)
    username = db.Column(db.String(length=20), nullable = False, unique = True)
    password_hash = db.Column(db.String(length=30), nullable = False)
    contact_number = db.Column(db.String(10), nullable= True, unique = True)
    address = db.Column(db.String(length=100), nullable = False)
    pincode = db.Column(db.String(6), nullable = False)
    is_admin = db.Column(db.Boolean(), default = 0)
    reservations = db.relationship('Reservation', backref = 'user', lazy = True)

    @property
    def password(self):
        return self.password_hash
    
    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password(self, password_to_check):
        return bcrypt.check_password_hash(self.password_hash, password_to_check)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ParkingLot(db.Model):
    lot_id = db.Column(db.Integer(), primary_key = True)
    primary_location = db.Column(db.String(length=20), nullable = False)
    full_address = db.Column(db.String(length=50), nullable = False)
    pincode = db.Column(db.String(6), nullable = False)
    max_spots = db.Column(db.Integer(), nullable = False)
    cost_per_unit = db.Column(db.Integer(), nullable = False)
    parking_spots = db.relationship('ParkingSpot', backref = 'lot', lazy= True)

    def available_spots(self):
        return sum(1 for spot in self.parking_spots if spot.status == 'A')


class ParkingSpot(db.Model):
    spot_id = db.Column(db.Integer(), primary_key = True)
    status = db.Column(db.String(1), default = 'A')
    lot_id = db.Column(db.Integer(), db.ForeignKey('parking_lot.lot_id'))
    spot_index = db.Column(db.Integer)
    reservations = db.relationship('Reservation', backref = 'spot', lazy = True)

class Reservation(db.Model):
    r_id = db.Column(db.Integer(), primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    spot_id = db.Column(db.Integer(), db.ForeignKey('parking_spot.spot_id'))
    checkin_time = db.Column(db.DateTime, default = datetime.utcnow)
    checkout_time = db.Column(db.DateTime, nullable = False)
    actual_checkout_time = db.Column(db.DateTime)
    vehicle_model = db.Column(db.String(length=20), nullable = False)
    nameplate_num = db.Column(db.String(15), nullable=False)
    cost_per_unit = db.Column(db.Float, nullable = False)
    estimated_cost = db.Column(db.Float, nullable = True)

    @property
    def total_cost(self):
        if not self.checkin_time:
            return 0  
        if self.checkout_time:
            end_time = self.actual_checkout_time or datetime.now()
        else:
            end_time = self.actual_checkout_time or datetime.now()

        parking_duration = end_time - self.checkin_time
        hours = parking_duration.total_seconds() // 3600
        return round(hours * self.cost_per_unit, 2)
    
    @property
    def parking_duration(self):
        if self.actual_checkout_time:
            end_time = self.actual_checkout_time or datetime.now()
        else:
            end_time = datetime.now()

        duration = end_time - self.checkin_time
        hours = max(1, duration.total_seconds() // 3600)
        return hours



