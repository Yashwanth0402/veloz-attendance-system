
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    send_file
)
from datetime import datetime, date
from flask import session, jsonify
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from database import db
from config import Config
from models import (
    Employee,
    Admin,
    Attendance
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


from datetime import date

def get_today_attendance(employee_id):

    today = date.today()

    attendance = Attendance.query.filter_by(
        employee_id=employee_id,
        date=today
    ).first()

    return attendance

def employee_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if "employee_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        if "admin_id" not in session:
            return redirect(url_for("admin_login"))

        return f(*args, **kwargs)

    return decorated

def get_active_attendance(employee_id):

    return Attendance.query.filter_by(
        employee_id=employee_id,
        clock_out_time=None
    ).order_by(
        Attendance.clock_in_time.desc()
    ).first()

@app.route("/")
def home():
    return redirect(url_for("login"))



# -------------------------
# DATABASE INIT
# -------------------------
@app.route("/init-db")
def init_db():

    db.create_all()

    return "Database Initialized"

@app.route("/admin/attendance")
def admin_attendance():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    attendances = Attendance.query.order_by(
        Attendance.date.desc()
    ).all()

    employees = Employee.query.all()

    return render_template(
        "admin_attendance.html",
        attendances=attendances,
        employees=employees
    )

@app.route("/admin/attendance/filter", methods=["POST"])
def filter_attendance():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    employee_id = request.form.get("employee_id")
    date = request.form.get("date")

    query = Attendance.query

    if employee_id and employee_id != "all":
        query = query.filter_by(employee_id=employee_id)

    if date:
        query = query.filter_by(date=date)

    attendances = query.order_by(
        Attendance.date.desc()
    ).all()

    employees = Employee.query.all()

    return render_template(
        "admin_attendance.html",
        attendances=attendances,
        employees=employees
    )

@app.route("/attendance/clockin", methods=["POST"])
def clock_in():

    employee_id = session.get("employee_id")

    if not employee_id:
        return jsonify({"message": "Not logged in"}), 401

    file = request.files.get("photo")

    print("FILES:", request.files)
    print("PHOTO:", file)

    if not file:
        return jsonify({
            "status": "error",
            "message": "No photo received"
        }), 400

    active_shift = Attendance.query.filter_by(
        employee_id=employee_id,
        clock_out_time=None
    ).first()

    if active_shift:
        return jsonify({
            "status": "error",
            "message": "Already clocked in. Please clock out first."
        })

    os.makedirs(
        os.path.join(app.root_path, "static/uploads/clockin"),
        exist_ok=True
    )

    filename = secure_filename(
        f"clockin_{datetime.now().timestamp()}.jpg"
    )

    filepath = os.path.join(
        app.root_path,
        "static",
        "uploads",
        "clockin",
        filename
    )

    file.save(filepath)

    attendance = Attendance(
        employee_id=employee_id,
        date=date.today(),
        clock_in_time=datetime.now(),
        clock_in_photo=f"uploads/clockin/{filename}",
        status="Working"
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Clocked in successfully"
    })

@app.route("/start-break")
def start_break():

    attendance = Attendance.query.filter_by(
    employee_id=session["employee_id"]
    ).order_by(
    Attendance.clock_in_time.desc()
    ).first()

    attendance.break_start = datetime.now()
    attendance.status = "On Break"

    db.session.commit()

    if attendance.break_start and not attendance.break_end:

        return {
           "status":"error",
           "message":"Already on break"
        }
   

    return {"status": "break started"}

@app.route("/end-break")
def end_break():

    attendance = Attendance.query.filter_by(
    employee_id=session["employee_id"]
    ).order_by(
    Attendance.clock_in_time.desc()
    ).first()

    attendance.break_end = datetime.now()
    attendance.status = "Working"

    db.session.commit()

    return {"status": "break ended"}


@app.route("/attendance/clockout", methods=["POST"])
def clock_out():

    employee_id = session.get("employee_id")

    file = request.files.get("photo")

    if not file:
        return jsonify({
            "status": "error",
            "message": "No photo received"
        }), 400

    attendance = Attendance.query.filter_by(
    employee_id=session["employee_id"]
    ).order_by(
       Attendance.clock_in_time.desc()
    ).first()

    attendance.clock_out_time = datetime.now()
    attendance.status = "Completed"

    if not attendance:
        return jsonify({
            "status": "error",
            "message": "No active session found"
        })

    os.makedirs(
        os.path.join(app.root_path, "static/uploads/clockout"),
        exist_ok=True
    )

    filename = secure_filename(
        f"clockout_{datetime.now().timestamp()}.jpg"
    )

    filepath = os.path.join(
        app.root_path,
        "static",
        "uploads",
        "clockout",
        filename
    )

    file.save(filepath)

    attendance.clock_out_photo = (
        f"uploads/clockout/{filename}"
    )

    attendance.clock_out_time = datetime.now()

    diff = (
        attendance.clock_out_time -
        attendance.clock_in_time
    )

    attendance.total_hours = round(
        diff.total_seconds() / 3600,
        2
    )

    attendance.status = "Completed"

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Clocked out successfully"
    })

@app.route("/admin/export/excel")
def export_excel():

    import pandas as pd

    data = []

    records = Attendance.query.all()

    for r in records:

        data.append({
            "Employee": r.employee.name,
            "Date": r.date,
            "Hours": r.total_hours
        })

    df = pd.DataFrame(data)

    file_path = "attendance_report.xlsx"

    df.to_excel(file_path,index=False)

    return send_file(
        file_path,
        as_attachment=True
    )

# -------------------------
# EMPLOYEE LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        pin = request.form["pin"]

        employees = Employee.query.all()

        employee = None

        for e in employees:
            if e.check_pin(pin):
                employee = e
                break

        if employee:

             if not employee.active:

                  flash(
                    "Your account has been disabled."
                   )

                  return redirect(
                      url_for("login")
                    )

             session["employee_id"] = employee.id

             return redirect(
                 url_for("dashboard")
                 )

        flash("Invalid PIN")

    return render_template("login.html")


# -------------------------
# EMPLOYEE DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():

    if "employee_id" not in session:
        return redirect(url_for("login"))

    employee = Employee.query.get(session["employee_id"])

    attendance = Attendance.query.filter_by(
          employee_id=session["employee_id"]
    ).order_by(
      Attendance.clock_in_time.desc()
    ).first()

    attendance_data = {
        "clock_in_time": None,
        "status": "Not Clocked In"
    }

    if attendance:
        attendance_data = {
            "clock_in_time": (
                attendance.clock_in_time.strftime("%H:%M:%S")
                if attendance.clock_in_time else None
            ),
            "status": attendance.status
        }

    return render_template(
        "dashboard.html",
        employee=employee,
        attendance=attendance_data
    )

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# -------------------------
# ADMIN LOGIN
# -------------------------
@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(
            username=username
        ).first()

        if admin and admin.check_password(password):

            session["admin_id"] = admin.id

            return redirect(
                url_for("admin_dashboard")
            )

        flash("Invalid Login")

    return render_template(
        "admin_login.html"
    )

@app.route("/my-attendance")
def my_attendance():

    if "employee_id" not in session:
        return redirect(url_for("login"))

    records = Attendance.query.filter_by(
        employee_id=session["employee_id"]
    ).order_by(Attendance.clock_in_time.desc()).all()

    return render_template(
        "my_attendance.html",
        records=records
    )
# -------------------------
# ADMIN DASHBOARD
# -------------------------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    total_employees = Employee.query.count()

    total_attendance = Attendance.query.count()
    
    working = Attendance.query.filter_by(
        status="Working"
    ).count()

    on_break = Attendance.query.filter_by(
        status="On Break"
    ).count()

    completed = Attendance.query.filter_by(
        status="Completed"
    ).count()

    employees = Employee.query.all()

    

    return render_template(
        "admin_dashboard.html",
        total_employees=total_employees,
        total_attendance=total_attendance,
        employees=employees
    )


@app.route("/admin/images")
def view_images():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    import os

    clockin_folder = os.listdir("static/uploads/clockin")
    clockout_folder = os.listdir("static/uploads/clockout")

    return render_template(
        "admin_images.html",
        clockin_images=clockin_folder,
        clockout_images=clockout_folder
    )


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_id",
        None
    )

    return redirect(
        url_for("admin_login")
    )

@app.route("/admin/toggle-employee/<int:id>")
def toggle_employee(id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    employee = Employee.query.get_or_404(id)

    employee.active = not employee.active

    db.session.commit()

    return redirect(url_for("employees"))


# -------------------------
# EMPLOYEE LIST
# -------------------------
@app.route("/admin/employees")
def employees():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    employee_list = Employee.query.all()

    return render_template(
        "employees.html",
        employees=employee_list
    )


# -------------------------
# ADD EMPLOYEE
# -------------------------
@app.route(
    "/admin/add-employee",
    methods=["POST"]
)
def add_employee():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    name = request.form["name"]
    pin = request.form["pin"]

    if len(pin) != 4 or not pin.isdigit():

        flash("PIN must be 4 digits")

        return redirect(
            url_for("employees")
        )

    employee = Employee(
        name=name
    )

    employee.set_pin(pin)

    db.session.add(employee)

    db.session.commit()

    flash("Employee Added")

    return redirect(
        url_for("employees")
    )


# -------------------------
# RESET PIN
# -------------------------
@app.route(
    "/admin/reset-pin/<int:id>",
    methods=["POST"]
)
def reset_pin(id):

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    employee = Employee.query.get_or_404(id)

    new_pin = request.form["pin"]

    if len(new_pin) != 4 or not new_pin.isdigit():

        flash("PIN must be 4 digits")

        return redirect(
            url_for("employees")
        )

    employee.set_pin(new_pin)

    db.session.commit()

    flash("PIN Updated")

    return redirect(
        url_for("employees")
    )


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5001
    )

