
from database import db
from werkzeug.security import generate_password_hash, check_password_hash


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    pin_hash = db.Column(db.String(255), nullable=False)

    active = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    attendances = db.relationship(
        "Attendance",
        backref="employee",
        lazy=True
    )

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(
            pin,
            method="pbkdf2:sha256"
        )

    def check_pin(self, pin):
        return check_password_hash(
            self.pin_hash,
            pin
        )

class Shift(db.Model):
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    employee = db.relationship(
        "Employee",
        backref="shift"
    )


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256"
        )

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )


class Attendance(db.Model):
    __tablename__ = "attendance"


    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employees.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        server_default=db.func.current_date(),
        nullable=False
    )

    clock_in_time = db.Column(db.DateTime)
    clock_in_photo = db.Column(db.String(255))

    clock_out_time = db.Column(db.DateTime)
    clock_out_photo = db.Column(db.String(255))

    break_start = db.Column(db.DateTime)
    break_end = db.Column(db.DateTime)

    gps_clock_in = db.Column(db.String(255))
    gps_clock_out = db.Column(db.String(255))

    late_minutes = db.Column(db.Integer, default=0)
    overtime_hours = db.Column(db.Float, default=0)

    total_hours = db.Column(db.Float, default=0)

    status = db.Column(
        db.String(50),
        default="Not Clocked In"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
