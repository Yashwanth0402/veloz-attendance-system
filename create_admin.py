
from flask import Flask
from config import Config
from models import Admin
from database import db
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():

    username = input("Admin Username: ")
    password = input("Admin Password: ")

    existing = Admin.query.filter_by(
        username=username
    ).first()

    if existing:
        print("Admin already exists.")
    else:
        admin = Admin(
            username=username
        )

        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print("Admin created successfully.")
