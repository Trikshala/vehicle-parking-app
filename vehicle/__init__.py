from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle.db'  
db.init_app(app)

with app.app_context():
    from vehicle.models import User
    db.create_all()
    if not User.query.filter_by(is_admin = True).first():
        admin = User(username = 'admin',password = 'admin-vp101',email_address = 'adminvp@gmail.com',conatct_number = '9988776655',address = 'Admin Headquarters, XYZ',is_admin = True)
        db.session.add(admin)
        db.session.commit()

