from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, Regexp
from vehicle.models import User

class RegistrationForm(FlaskForm):
    username = StringField(label="Username: ",validators=[Length(min=2,max=20),DataRequired()])
    pass_1 = PasswordField(label="Password: ",validators=[Length(min=6, max=30),DataRequired()])
    pass_2 = PasswordField(label="Confirm Password: ",validators=[EqualTo('pass_1'),DataRequired()])
    email_address = StringField(label="Email Address: ",validators=[Email(),DataRequired()])
    contact_number = StringField(label="Contact Number: ",validators=[DataRequired(message="Contact number is required."),Length(min=10, max=10, message="Contact number must be exactly 10 digits."),Regexp(r'^\d{10}$', message="Contact number must contain only digits.")])
    address = StringField(label="Address: ",validators=[Length(min=2,max=50),DataRequired()])
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

    