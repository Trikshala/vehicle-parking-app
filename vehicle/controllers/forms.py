from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DecimalField, SelectField, HiddenField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, Regexp, NumberRange
from vehicle.models import User, ParkingLot

class RegistrationForm(FlaskForm):
    first_name = StringField(label="First Name: ",validators=[DataRequired()])
    last_name = StringField(label="Last Name: ",validators=[DataRequired()])
    email_address = StringField(label="Email Address: ",validators=[Email(),DataRequired()])
    username = StringField(label="Username: ",validators=[Length(min=2,max=20),DataRequired()])
    pass_1 = PasswordField(label="Password: ",validators=[Length(min=6, max=30),DataRequired()])
    pass_2 = PasswordField(label="Confirm Password: ",validators=[EqualTo('pass_1'),DataRequired()])
    contact_number = StringField(label="Contact Number: ",validators=[DataRequired(message="Contact number is required."),Length(min=10, max=10, message="Contact number must be exactly 10 digits."),Regexp(r'^\d{10}$', message="Contact number must contain only digits.")])
    address = StringField(label="Address: ",validators=[Length(min=2,max=50),DataRequired()])
    pincode = StringField(label="Pin Code: ",validators=[Length(min=6,max=6, message="PinCode must be exactly 6 digits."),Regexp(r'^\d{6}$', message="PinCode must contain only digits."),DataRequired(message="PinCode is required.")])
    submit = SubmitField(label="Register")

    def validate_username(self, username_to_check):
        user = User.query.filter_by(username = username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try another one.')
        
    def validate_email_address(self, email_to_check):
        email_address = User.query.filter_by(email_address = email_to_check.data).first()
        if email_address:
            raise ValidationError('Email address already exists! Check your details properly.')

class LoginForm(FlaskForm):
    username = StringField(label="Username: ")
    pass_1 = PasswordField(label="Password: ")
    submit = SubmitField(label="Login")

class CreateParkingLotForm(FlaskForm):
    primary_location = StringField(label="Prime Location Name: ",validators=[Length(min=2,max=20),DataRequired()])
    full_address = StringField(label="Full Address: ",validators=[Length(min=2,max=50),DataRequired()])
    pincode = StringField(label="Pin Code: ",validators=[Length(min=6,max=6, message="PinCode must be exactly 6 digits."),Regexp(r'^\d{6}$', message="PinCode must contain only digits."),DataRequired(message="PinCode is required.")])
    cost_per_unit = DecimalField(label="Price (per hour):", validators=[DataRequired(), NumberRange(min=25,message="Price cannot be negative.")])
    max_spots = IntegerField(label="Maximun spots: ", validators=[DataRequired(),NumberRange(min=10,max=40)])
    submit = SubmitField(label="Create Parking Lot")

    def __init__(self, original_id = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_id = original_id


class DeleteParkingLotForm(FlaskForm):
    submit = SubmitField(label="Delete Parking Lot")

class SearchParkingLot(FlaskForm):
    location = SelectField(label = 'Select Location', choices = [])
    submit = SubmitField(label="Search")

class BookingForm(FlaskForm):
    lot_id = StringField(label = 'Lot Id', render_kw={'read_only': True})
    spot_id = StringField(label = 'Lot Id', render_kw={'read_only': True})
    user_id = StringField(label = 'Lot Id', render_kw={'read_only': True})
    cost_per_hour = StringField(label = 'Lot Id', render_kw={'read_only': True})
    no_of_hours = IntegerField(label='Number of hours:', validators=[DataRequired()])
    vehicle_model = StringField(label='Vehicle Model:', validators=[DataRequired()])
    vehicle_number = StringField(label='Vehicle Number:', validators=[DataRequired()])
    submit = SubmitField('Book The Spot')

class ReleaseSpotForm(FlaskForm):
    r_id = HiddenField()
    submit = SubmitField(label='Release')

class EditProfileForm(FlaskForm):
    first_name = StringField(label="First Name: ",validators=[DataRequired()])
    last_name = StringField(label="Last Name: ")
    email_address = StringField(label="Email Address: ",validators=[Email(),DataRequired()])
    contact_number = StringField(label="Contact Number: ",validators=[Length(min=10, max=10, message="Contact number must be exactly 10 digits."),Regexp(r'^\d{10}$', message="Contact number must contain only digits.")])
    address = StringField(label="Address: ",validators=[Length(min=2,max=50)])
    pincode = StringField(label="Pin Code: ",validators=[Length(min=6,max=6, message="PinCode must be exactly 6 digits."),Regexp(r'^\d{6}$', message="PinCode must contain only digits.")])
    submit = SubmitField(label="Edit Profile")

class AdminSearchForm(FlaskForm):
    search_choice = SelectField(label = 'Search by', choices = [('u_id', 'User ID'), ('loc', 'Location Name')])
    search_string = StringField(label="Search by Keyword", validators=[DataRequired()])
    submit = SubmitField(label="Search")

    def validate_search(self, value):
        search_choice = self.search_choice.data
        search_string = value.data.strip()

        if search_choice == 'u_id':
            try:
                search_string = int(search_string)
            except ValueError:
                raise ValidationError("User ID must be an integer.")
            if not User.query.get(search_string):
                raise ValidationError("User not found in database.")
            
        elif search_choice == 'loc':
            if not ParkingLot.query.filter_by(primary_location = search_string).first():
                raise ValidationError("Location not found.")



    