from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate

@event.listens_for(Engine, "connect")
def enforce_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):  # Only runs for SQLite
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

db = SQLAlchemy()
migrate = Migrate()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicle.db'  
app.config['SECRET_KEY'] = 'a7d09d781f30ce21722f71f0e69e34'
db.init_app(app)
migrate.init_app(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category="info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    from vehicle.models import User
    db.create_all()
    if not User.query.filter_by(is_admin = True).first():
        admin = User(first_name = 'John', last_name = 'Doe',email_address = 'adminvp@gmail.com',username = 'admin',contact_number = '9988776655',address = 'Admin Headquarters, XYZ', pincode = '501011',is_admin = True)
        admin.password= 'admin-vp101'
        db.session.add(admin)
        db.session.commit()

from vehicle.controllers import routes
