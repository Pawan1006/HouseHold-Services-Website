from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User, Professional, Admin, Service
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import os

# Create a Blueprint for authentication routes
auth = Blueprint('auth', __name__)

# Define the login route
@auth.route('/', methods=['GET', 'POST'])
def login():
    # If the form is submitted then get detalis
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        status = request.form.get("status")
        
        # Query the database for user, admin, and professional by email
        user = User.query.filter_by(email=email).first()
        admin = Admin.query.filter_by(email=email).first()
        prof = Professional.query.filter_by(email=email).first()

        # Check if the user/admin/professional exists
        if user:
            if user.status != "blocked":
                if check_password_hash(user.password, password):
                    flash("Logged in successfully!", category="success")
                    login_user(user, remember=True)
                    return redirect(url_for("views.customer_dashboard"))
                else:
                    flash("Incorrect password.", category="error")
            else:
                flash("Your account is BLOCKED", category="error") 
        elif admin:
            if (admin.password == password):
                flash("Logged in successfully!", category="success")
                login_user(admin, remember=True)
                return redirect(url_for("views.admin_dashboard"))
            else:
                flash("Incorrect password.", category="error")
        elif prof:
            if prof.status != "blocked":
                if check_password_hash(prof.password, password):
                    flash("Logged in successfully!", category="success")
                    login_user(prof, remember=True)
                    return redirect(url_for("views.professional_dashboard"))
                else:
                    flash("Incorrect password.", category="error")
            else:
               flash("Your account is BLOCKED", category="error") 
        else:
            flash("User does not exist.", category="error")
        
        
    return render_template('login.html')

# Define the logout route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", category="success")
    return redirect(url_for("auth.login"))

# Define the signup route for customers
@auth.route('/sign-up', methods=['GET', 'POST'])
def customerSignup():
    if request.method == 'POST':
        email = request.form.get('email')
        fullName = request.form.get('fullName')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Check if the email already exists
        user = User.query.filter_by(email=email).first()
        
         # Validate the input fields
        if user:
            flash("Email already exists.", category="error")
        elif len(email) <= 5:
            flash("Email must be greater than 5 characters.", category="error")
        elif len(fullName) < 2:
            flash("Name must be greater than 1 characters.", category="error")
        elif len(address) <= 2:
            flash("Address must be greater than 2 characters.", category="error")
        elif len(pincode) != 6:
            flash("Pin Code must be equal to 6 digits.", category="error")
        elif len(password1) < 5:
            flash("Password must be at least 4 characters.", category="error")
        elif password1 != password2:
            flash("Password must be same.", category="error")
        else:
            # Create a new user and hash the password
            new_user = User(email=email, full_name=fullName, address=address, pincode=pincode, password=generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash("Account created!", category="success")
            return redirect(url_for("auth.login"))

    return render_template('customerSignup.html')

# Define the signup route for professionals
@auth.route("/professional-signUp", methods=["GET", "POST"])
def professionalSignup():
    services = Service.query.all()
    service_data = None
    base_price = None

    if request.method == 'POST':
        email = request.form.get('email')
        fullName = request.form.get('fullName')
        address = request.form.get('address')
        service = request.form.get('service')
        experience = request.form.get('experience')
        pincode = request.form.get('pincode')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        pdf_file = request.files.get('pdf')
        price = request.form.get('price')

        # Get the base price for the selected service
        service_data = Service.query.filter_by(service=service).first()
        if service_data:
            base_price = service_data.price

        # Check if professional already exists
        user = Professional.query.filter_by(email=email).first()
        
         # Validate the input fields
        if user:
            flash("Email already exists.", category="error")
        elif len(email) <= 5:
            flash("Email must be greater than 5 characters.", category="error")
        elif len(fullName) < 2:
            flash("Name must be greater than 1 characters.", category="error")
        elif len(address) <= 2:
            flash("Address must be greater than 2 characters.", category="error")
        elif not service:
            flash("Please Select Service.", category="error") 
        elif not experience.isnumeric() or int(experience) < 0:
            flash("Experience cannot be negative or invalid.", category='error')
        elif int(price) < int(base_price):
            flash("Price can not be less than base price!", category="error")
        elif len(pincode) != 6:
            flash("Pin Code must be equal to 6 digits.", category="error")
        elif len(password1) < 5:
            flash("Password must be at least 4 characters.", category="error")
        elif password1 != password2:
            flash("Password must be same.", category="error")
        elif pdf_file and pdf_file.filename:
            # Save PDF file
            if not pdf_file.filename.endswith('.pdf'):
                flash("Please upload a file with a .pdf extension.", category="error")
            elif pdf_file.content_type != 'application/pdf':
                flash("Uploaded file is not a valid PDF.", category="error")
            else:
                # Save the uploaded PDF file securely
                pdf_filename = secure_filename(pdf_file.filename)
                upload_folder = os.path.join(current_app.root_path, 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                pdf_path = os.path.join(upload_folder, pdf_filename)
                pdf_file.save(pdf_path)

                # Create a new Professional user and hash the password
                new_user = Professional(email=email, 
                                    full_name=fullName, 
                                    address=address, 
                                    service=service, 
                                    experience=experience, 
                                    pincode=pincode,
                                    price=price,
                                    pdf_file_path=pdf_filename,
                                    password=generate_password_hash(password1, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                flash("Registration Successful! Your request is pending approval.", category="success")
                return redirect(url_for("auth.login"))
        else:
            flash("Please upload a valid PDF file.", category="error")

    return render_template("professionalSignup.html", services=services, service_data=service_data, base_price=base_price)