from flask import Blueprint, render_template, flash, request, redirect, url_for, Response, send_from_directory
from flask_login import login_required, current_user
from .models import Service, Professional, User, Request
from . import db
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime
import pytz
from sqlalchemy import or_, extract, func
from sqlalchemy.orm import joinedload
import numpy as np


# Blueprint for views
views = Blueprint("views", __name__)

# Customer Dashboard View
# Route to display the customer dashboard with user services and requests.
@views.route("/customer-dashboard")
@login_required
def customer_dashboard():
    requests = Request.query.all()
    services = Service.query.all()
    user = User.query.get(current_user.id)
    return render_template("user_dash.html", services=services, user=user, requests=requests)


# Route to display and update user profile.
@views.route("/user-profile/<int:Id>", methods=["GET", "POST"])
@login_required
def user_profile(Id):
    if request.method == "POST":
        email = request.form.get("email")
        full_name = request.form.get("name")
        address = request.form.get("address")
        pincode = request.form.get("pincode")

        update_profile = User.query.filter_by(id=Id).first()
        update_profile.email = email
        update_profile.full_name = full_name
        update_profile.address = address
        update_profile.pincode = pincode
        db.session.add(update_profile)
        db.session.commit()
        flash("Profile updated successfully!", category="success")
        return redirect(url_for("views.customer_dashboard"))
    user = User.query.filter_by(id=Id).first()
    return render_template("user_profile.html", user=user)


# Route to handle searching by requests, services, or pincode for users.
@views.route("/user-search", methods=["GET"])
@login_required
def user_search():
    search_type = request.args.get("search_type")
    query = request.args.get("query")
    results = []
    search_performed = False

    if search_type:
        search_performed = True
        if search_type == "requests":
            if query:
                results = search_by_request(query)
            else:
                results = Request.query.filter_by(customer_id=current_user.id).all() 
        elif search_type in ["services", "pincode"]:
            if query:
                results = search_by(query)
            else:
                results = get_all_professionals()
    user = User.query.get(current_user.id)
    return render_template("user_search.html", results=results, search_performed=search_performed, search_type=search_type, user=user)

# Helper function to filter requests by customer, service, or status.
def search_by_request(query):
    return Request.query.join(Professional).filter(
        Request.customer_id == current_user.id,
        or_(
            Professional.full_name.ilike(f'%{query}%'),
            Professional.service.ilike(f'%{query}%'),
            Professional.price.ilike(f'%{query}%'),
            Request.service_status.ilike(f'%{query}%')
        )
    ).options(joinedload(Request.professional)).all()

# Helper function to filter services or pincode search.
def search_by(query):
    return Professional.query.filter(or_(Professional.full_name.ilike(f'%{query}%'),
                                        Professional.service.ilike(f'%{query}%'),
                                        Professional.pincode.ilike(f'%{query}%'),
                                        Professional.price.ilike(f'%{query}%'))).all()


# Route to display summary information for the user.
@views.route("/user-summary")
@login_required
def user_summary():
    user = User.query.get(current_user.id)
    return render_template("user_summary.html",user = user)

# Route to display services and related professionals for users.
@views.route("/show-services/<int:id>", methods=["GET", "POST"])
@login_required
def show_services(id):
    user = User.query.get(current_user.id)
    user_id = current_user.id
    requests = Request.query.filter_by(customer_id=user_id).all()
    service = Service.query.filter_by(id=id).first()
    professionals = Professional.query.filter_by(service=service.service).all()
    return render_template("show_services.html", profs=professionals, requests=requests, service=service, user=user)


# Route to handle booking of services for users.
@views.route("/book_service/<int:prof_id>", methods=['GET', 'POST'])
@login_required
def book_service(prof_id):
    if request.method == 'POST':
        user_id = current_user.id
        profs = Professional.query.filter_by(id=prof_id).first()
        service = Service.query.filter_by(service=profs.service).first()
        new_request = Request(service_id=service.id, professional_id=profs.id, customer_id=user_id, service_status="pending")
        db.session.add(new_request)
        db.session.commit()
        flash('Service booked successfully!', category='success')
        return redirect(url_for("views.show_services", id=service.id))

    user = current_user
    return render_template("user_dash.html", user=user)



# Route to allow users to cancel a service request.
@views.route("show_services/cancel_request/<int:request_id>", methods=['POST'])
@login_required
def service_cancel_request(request_id):
    request_to_cancel = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if request_to_cancel and request_to_cancel.service_status == "pending":
        request_to_cancel.service_status = "cancelled"
        db.session.commit()
        flash('Request cancelled successfully!', category='success')
    else:
        flash('Request not found or cannot be cancelled.', category='error')

    return redirect(url_for("views.show_services", id=request_to_cancel.service_id))


# Route to allow users to cancel a service request.
@views.route("cancel_request/<int:request_id>", methods=['POST'])
@login_required
def cancel_request(request_id):
    request_to_cancel = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if request_to_cancel and request_to_cancel.service_status == "pending":
        request_to_cancel.service_status = "cancelled"
        db.session.commit()
        flash('Request cancelled successfully!', category='success')
    else:
        flash('Request not found or cannot be cancelled.', category='error')

    return redirect(url_for("views.customer_dashboard"))


# Route to handle service closure, remarks, and ratings.
@views.route("/close_service/<int:request_id>", methods=["GET", "POST"])
@login_required
def close_request(request_id):
    request_to_close = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if request.method == "POST":
        rating = request.form.get("rating")
        remark = request.form.get("remark")
        if request_to_close and request_to_close.service_status == "accepted":
            request_to_close.service_status = "closed"
            request_to_close.date_of_completion = datetime.now(pytz.timezone('Asia/Kolkata'))
            request_to_close.rating = rating
            request_to_close.remarks = remark
            db.session.commit()
            flash('Service closed successfully!', category='success')
            return redirect(url_for("views.customer_dashboard"))
    user = User.query.get(current_user.id) 
    return render_template("service_remark.html", requests=request_to_close, user=user)


# Route to handle update remarks and ratings.
@views.route("/update_remark/<int:request_id>", methods=["GET", "POST"])
@login_required
def update_remark(request_id):
    remark_update = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if request.method == "POST":
        rating = request.form.get("rating")
        remark = request.form.get("remark")
        if remark_update and remark_update.service_status == "closed":
            remark_update.rating = rating
            remark_update.remarks = remark
            db.session.commit()
            flash('Remark updated successfully!', category='success')
            return redirect(url_for("views.customer_dashboard"))
    user = User.query.get(current_user.id) 
    return render_template("update_remark.html", requests=remark_update, user=user)


# Route to display dashboard for professionals based on their approval status.
@views.route("/professional-dashboard")
@login_required
def professional_dashboard():
    prof_id = current_user.id
    professional = Professional.query.filter_by(id=prof_id).first()
    requests = Request.query.filter_by(professional_id=professional.id).all()
    
    if professional.status == "pending":
        return render_template("pending.html", prof=professional)
    elif professional.status == "approved":
        return render_template("prof_dash.html", prof=professional, requests=requests)
    elif professional.status == "rejected":
        return render_template("rejected.html", prof=professional)


# Route to allow professionals to resend their registration request.
@views.route("/resend", methods=["GET", "POST"])
def resend():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = Professional.query.filter_by(email=email).first()
        if existing_user:
            existing_user.status = 'pending'
            db.session.commit()
            flash('Your registration request has been resent.', category="success")
            return render_template("pending.html")
        

# Route to handle search requests for professionals.
@views.route("/prof-search")
@login_required
def prof_search():
    prof_id = current_user.id
    professional = Professional.query.filter_by(id=prof_id).first()
    search_type = request.args.get("search_type")
    query = request.args.get("query")
    results = []
    search_performed = False

    if search_type:
        search_performed = True
        if query:
            results = request_search_by(search_type, query)
        else:
            results = get_all_requests()
    return render_template("prof_search.html",prof_id=prof_id, prof=professional, results=results, search_performed=search_performed, search_type=search_type)

# Helper function to filter search results based on the type of search and query.
def request_search_by(search_type, query):
    if search_type == "date":
        # Check if the query is in the format dd-mm
        if len(query) == 5 and query[2] == '-':
            try:
                day, month = map(int, query.split('-'))
                return Request.query.filter(
                    extract('day', Request.date_of_request) == day,
                    extract('month', Request.date_of_request) == month
                ).options(joinedload(Request.customer)).all()
            except ValueError:
                return []  # Return empty if day/month conversion fails

        # Check if the query is just dd (single day)
        elif len(query) == 2:
            try:
                day = int(query)
                return Request.query.filter(
                    extract('day', Request.date_of_request) == day
                ).options(joinedload(Request.customer)).all()
            except ValueError:
                return []  # Return empty if day conversion fails

        # Check if the query is in the format dd-mm-yyyy
        elif len(query) == 10 and query[2] == '-' and query[5] == '-':
            try:
                # Parse the input date
                search_date = datetime.strptime(query, '%d-%m-%Y')
                # Make it timezone-aware (Asia/Kolkata)
                search_date = pytz.timezone('Asia/Kolkata').localize(search_date)
                
                # Create a date object for comparison
                date_only = search_date.date()
                return Request.query.filter(
                    func.date(Request.date_of_request) == date_only  # Compare just the date part
                ).options(joinedload(Request.customer)).all()
            except ValueError:
                return []  # Return empty if date format is incorrect

        # If the query doesn't match expected formats, return empty
        return []

    # Default behavior for other search types
    return Request.query.join(Request.customer).filter(
        or_(
            User.full_name.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%'),
            User.address.ilike(f'%{query}%'),
            User.pincode.ilike(f'%{query}%'),
            Request.rating.ilike(f'%{query}%'),
            Request.service_status.ilike(f'%{query}%')
        )
    ).options(joinedload(Request.customer)).all()


# Route to display base prices for all services
@views.route("/list/basePrice")
def base_price():
    services = Service.query.all()
    return render_template("base_price.html", services=services)


# Route to render the professional summary page 
@views.route("/prof-summary")
@login_required
def prof_summary():
    prof = Professional.query.get(current_user.id)
    return render_template("prof_summary.html", prof=prof)


# Route to handle file uploads
@views.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


# Route to display and update professional profile 
@views.route("/prof-profile/<int:Id>", methods=["GET", "POST"])
@login_required
def prof_profile(Id):
    if request.method == "POST":
        email = request.form.get("email")
        full_name = request.form.get("name")
        service = request.form.get("service")
        experience = request.form.get("experience")
        address = request.form.get("address")
        pincode = request.form.get("pincode")
        price = request.form.get("price")
        desc = request.form.get("desc")

        update_profile = Professional.query.filter_by(id=Id).first()
        update_profile.email = email
        update_profile.full_name = full_name
        update_profile.service = service
        update_profile.expirence = experience
        update_profile.address = address
        update_profile.pincode = pincode
        update_profile.price = price
        update_profile.desc = desc
        db.session.add(update_profile)
        db.session.commit()
        flash("Profile updated successfully!", category="success")
        return redirect(url_for("views.professional_dashboard"))
    profiles = Professional.query.filter_by(id=Id).first()
    service = Service.query.filter_by(service=profiles.service).first()
    return render_template("prof_profile.html", profiles=profiles, service=service)


# Route to accept a service request
@views.route("/request/accept/<int:request_id>", methods=['POST'])
@login_required
def accept_request(request_id):
    request_to_accept = Request.query.get(request_id)
    request_to_accept.professional_id = current_user.id
    request_to_accept.service_status = 'accepted'
    db.session.commit()
    flash('Request accepted!', category="success")
    return redirect(url_for("views.professional_dashboard"))


# Route to reject a service request 
@views.route("/request/reject/<int:request_id>", methods=['POST'])
@login_required
def reject_request(request_id):
    request_to_reject = Request.query.get(request_id)
    request_to_reject.service_status = 'rejected'
    db.session.commit()
    flash('Request rejected!', category="success")
    return redirect(url_for("views.professional_dashboard"))


# Route to close a service request
@views.route("/request/close/<int:request_id>", methods=['POST'])
@login_required
def prof_close_service(request_id):
    close_service = Request.query.get(request_id)
    close_service.service_status = 'closed'
    close_service.date_of_completion = datetime.now(pytz.timezone('Asia/Kolkata'))
    db.session.commit()
    flash('Request closed!', category="success")
    return redirect(url_for("views.professional_dashboard"))

        
# Admin route to display dashboard with services, professionals, and requests 
@views.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    service = Service.query.all()
    professionals = Professional.query.all()
    requests = Request.query.all()
    return render_template("admin_dash.html", service=service, professionals=professionals, requests=requests)


# Admin route to handle search queries for customers, professionals, requests, and services 
@views.route("/admin/search", methods=["GET"])
@login_required
def admin_search():
    search_type = request.args.get("search_type", "")
    query = request.args.get("query", "")
    results = []
    search_performed = bool(query) or bool(search_type)

    if search_type:
        if search_type == "customer":
            if query:
                results = search_customers(query)
            else:
                results = get_all_customers()

        elif search_type == "professional":
            if query:
                results = search_professionals(query)
            else:
                results = get_all_professionals()

        elif search_type == "request":
            if query:
                results = search_requests(query)
            else:
                results = get_all_requests()

        elif search_type == "service":
            if query:
                results = search_services(query)
            else:
                results = get_all_services()
    return render_template("admin_search.html", results=results, search_type=search_type, search_performed=search_performed, query=query)


def search_customers(query):
    return User.query.filter(or_(User.full_name.ilike(f'%{query}%'), User.status.ilike(f'%{query}%'))).all()

def get_all_customers():
    return User.query.all()

def search_professionals(query):
    return Professional.query.filter(or_(Professional.full_name.ilike(f'%{query}%'), Professional.status.ilike(f'%{query}%'))).all()

def get_all_professionals():
    return Professional.query.all()

def search_requests(query):
    return Request.query.join(Request.professional).filter(or_(Professional.full_name.ilike(f'%{query}%'),Request.service_status.ilike(f'%{query}%'))).options(joinedload(Request.professional)).all()

def get_all_requests():
    return Request.query.options(db.joinedload(Request.professional)).all()

def search_services(query):
    return Service.query.filter(or_(Service.service.ilike(f'%{query}%'), Service.price.ilike(f'%{query}%'))).all()

def get_all_services():
    return Service.query.all()


# Admin route to display summary page
@views.route("/admin/summary")
@login_required
def admin_summary():
    return render_template("admin_summary.html")


# Route to display professional details based on ID 
@views.route("/professional/details/<int:id>")
@login_required
def prof_details(id):
    profiles = Professional.query.filter_by(id=id).first()
    return render_template("prof_details.html", profiles=profiles)


# Route to display service request details for a specific service ID 
@views.route("/service/details/<int:id>")
@login_required
def service_details(id):
    requests = Request.query.filter_by(service_id=id).all()
    return render_template("service_requested_details.html", requests=requests)


# Route to add a new service
@views.route("/service-add", methods=["GET", "POST"])
@login_required
def service_add():
    if request.method == "POST":
        service = request.form.get("service")
        desc = request.form.get("desc")
        price = request.form.get("price")

        if len(service) < 1:
            flash("Please add service.", category = "error")
        elif len(price) == 0:
            flash("Add Price", category = "error")
        else:
            new_service = Service(service=service, desc=desc, price=price)
            db.session.add(new_service)
            db.session.commit()
            flash("Service added successfully!", category="success")
            return redirect(url_for("views.admin_dashboard"))
    return render_template("addService.html")


# Route to delete a service by ID 
@views.route("/admin/deleteService/<int:Id>")
@login_required
def delete_service(Id):
    remove_service = Service.query.filter_by(id=Id).first()
    remove_request = Request.query.filter_by(service_id=Id).all()
    remove_prof = Professional.query.filter_by(service=remove_service.service).all()
    for request in remove_request:
        db.session.delete(request)
    for professional in remove_prof:
        db.session.delete(professional)
    db.session.delete(remove_service)
    db.session.commit()
    flash("Service removed successfully!", category="success")
    return redirect(url_for("views.admin_dashboard"))


# Route to delete a service by ID 
@views.route("/admin/search/deleteService/<int:id>")
@login_required
def search_delete(id):
    remove_service = Service.query.filter_by(id=id).first()
    remove_request = Request.query.filter_by(service_id=id).all()
    remove_prof = Professional.query.filter_by(service=remove_service.service).all()
    for r in remove_request:
        db.session.delete(r)
    for professional in remove_prof:
        db.session.delete(professional)
    db.session.delete(remove_service)
    db.session.commit()
    flash("Service removed successfully!", category="success")
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')
    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


# Route to update a service by ID 
@views.route("/admin/update/<int:Id>", methods=["GET", "POST"])
@login_required
def update(Id):
    if request.method == "POST":
        service = request.form.get("service")
        desc = request.form.get("desc")
        price = request.form.get("price")

        update_service = Service.query.filter_by(id=Id).first()
        update_service.service = service
        update_service.desc = desc
        update_service.price = price
        db.session.add(update_service)
        db.session.commit()
        flash("Service updated successfully!", category="success")
        return redirect(url_for("views.admin_dashboard"))
    service = Service.query.filter_by(id=Id).first()
    return render_template("updateService.html", service=service)


# Route to update a service by ID 
@views.route("/admin/search/update/<int:id>", methods=["GET", "POST"])
@login_required
def search_update(id):
    if request.method == "POST":
        service = request.form.get("service")
        desc = request.form.get("desc")
        price = request.form.get("price")

        update_service = Service.query.filter_by(id=id).first()
        update_service.service = service
        update_service.desc = desc
        update_service.price = price
        db.session.add(update_service)
        db.session.commit()
        flash("Service updated successfully!", category="success")
        query = request.args.get('query', '')
        search_type = request.args.get('search_type', '')
        return redirect(url_for("views.admin_search", query=query, search_type=search_type))
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')
    service = Service.query.filter_by(id=id).first()
    return render_template("updateService.html", query=query, search_type=search_type, service=service)


# Route to approve a professional by ID 
@views.route("/admin/approve/<int:id>")
@login_required
def approve_professional(id):
    user = Professional.query.get(id)
    if user:
        user.status = "approved"
        db.session.commit()
        flash(f'Professional {user.full_name} approved.')
    return redirect(url_for("views.admin_dashboard"))


# Route to delete a professional by ID 
@views.route("/admin/delete/professional/<int:Id>")
@login_required
def delete_professional(Id):
    remove_prof = Professional.query.filter_by(id=Id).first()
    if remove_prof.status == "pending":
        db.session.delete(remove_prof)
        db.session.commit()
        flash("Professional request removed successfully!", category="success")
        return redirect(url_for('views.admin_dashboard'))
    else:
        db.session.delete(remove_prof)
        db.session.commit()
        flash("Professional removed successfully!", category="success")
        return redirect(url_for('views.admin_dashboard'))


# Route to delete a professional by ID 
@views.route("/admin/delete/prof/<int:Id>")
@login_required
def delete_prof(Id):
    remove_prof = Professional.query.filter_by(id=Id).first()
    remove_request = Request.query.filter_by(professional_id=Id).all()
    for r in remove_request:
        db.session.delete(r)
    db.session.delete(remove_prof)
    db.session.commit()
    flash("Professional removed successfully!", category="success")
    return redirect(url_for('views.prof_status'))


# Route to reject a professional by ID 
@views.route("/admin/reject/<int:id>")
@login_required
def reject_professional(id):
    prof = Professional.query.get(id)
    if prof:
        prof.status = "rejected"
        db.session.commit()
        flash(f'Professional {prof.full_name} request rejected.')
    return redirect(url_for("views.admin_dashboard"))


# Route to block a professional by ID 
@views.route("/admin/block/professional/<int:id>")
@login_required
def block_professional(id):
    prof = Professional.query.get(id)
    if prof:
        prof.status = "blocked"
        db.session.commit()
        flash(f'Professional {prof.full_name} Blocked.')
    return redirect(url_for("views.prof_status"))


# Route to block a professional in the search result 
@views.route("/admin/search/block/professional/<int:id>")
@login_required
def search_block_professional(id):
    prof = Professional.query.get(id)
    if prof:
        prof.status = "blocked"
        db.session.commit()
        flash(f'Professional {prof.full_name} Blocked.')

    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')
    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


# Route to unblock a professional in the search result 
@views.route("/admin/search/unblock/professional/<int:id>")
@login_required
def search_unblock_professional(id):
    prof = Professional.query.get(id)
    if prof:
        prof.status = "approved"
        db.session.commit()
        flash(f'Professional {prof.full_name} Unblocked.')

    # Retrieve current search parameters
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')

    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


# Route to unblock a professional by ID 
@views.route("/admin/unblock/professional/<int:id>")
@login_required
def unblock_professional(id):
    prof = Professional.query.get(id)
    if prof:
        prof.status = "approved"
        db.session.commit()
        flash(f'Professional {prof.full_name} Unblocked.')
    return redirect(url_for("views.prof_status"))

# Route to Delete a Prof by ID
@views.route("/admin/search/delete/professional/<int:id>")
@login_required
def delete_prof_by_search(id):
    prof = Professional.query.get(id)   
    remove_request = Request.query.filter_by(professional_id=id).all()
    for r in remove_request:
        db.session.delete(r)
    db.session.delete(prof)
    db.session.commit()
    flash(f'Professional {prof.full_name} has been deleted.')

    # Retrieve current search parameters
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')

    return redirect(url_for("views.admin_search", query=query, search_type=search_type))



# Route to view all professionals' statuses 
@views.route("/professional/status")
@login_required
def prof_status():
    professionals = Professional.query.all()
    return render_template("prof_status.html", professionals=professionals)


# Route to view all customers' statuses 
@views.route("/customer/status")
@login_required
def cust_status():
    users = User.query.all()
    return render_template("cust_status.html", users=users)


# Route to block a customer by ID 
@views.route("/admin/block/customer/<int:id>")
@login_required
def block_customer(id):
    user = User.query.get(id)
    if user:
        user.status = "blocked"
        db.session.commit()
        flash(f'User {user.full_name} Blocked.')
    return redirect(url_for("views.cust_status"))


# Route to unblock a customer by ID 
@views.route("/admin/unblock/customer/<int:id>")
@login_required
def unblock_customer(id):
    user = User.query.get(id)
    if user:
        user.status = "active"
        db.session.commit()
        flash(f'User {user.full_name} Unblocked.')
    return redirect(url_for("views.cust_status"))


# Route to Block a Customer by ID
@views.route("/admin/search/block/customer/<int:id>")
@login_required
def search_block_customer(id):
    user = User.query.get(id)
    if user:
        user.status = "blocked"
        db.session.commit()
        flash(f'User {user.full_name} Blocked.')

    # Retrieve current search parameters
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')

    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


# Route to Unblock a Customer by ID
@views.route("/admin/search/unblock/customer/<int:id>")
@login_required
def search_unblock_customer(id):
    user = User.query.get(id)
    if user:
        user.status = "active"
        db.session.commit()
        flash(f'User {user.full_name} Unblocked.')

    # Retrieve current search parameters
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')

    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


# Route to Delete a Customer by ID
@views.route("/admin/delete/customer/<int:id>")
@login_required
def delete_customer(id):
    user = User.query.get(id)
    remove_request = Request.query.filter_by(customer_id=id).all()
    for r in remove_request:
        db.session.delete(r)
    db.session.delete(user)
    db.session.commit()
    flash(f'Customer {user.full_name} has been deleted.')
    return redirect(url_for('views.cust_status'))


# Route to Delete a Customer by ID
@views.route("/admin/search/delete/customer/<int:id>")
@login_required
def delete_customer_by_search(id):
    user = User.query.get(id)   
    remove_request = Request.query.filter_by(customer_id=id).all()
    for r in remove_request:
        db.session.delete(r)
    db.session.delete(user)
    db.session.commit()
    flash(f'Customer {user.full_name} has been deleted.')

    # Retrieve current search parameters
    query = request.args.get('query', '')
    search_type = request.args.get('search_type', '')

    return redirect(url_for("views.admin_search", query=query, search_type=search_type))


@views.route("/request/details/<int:id>")
@login_required
def request_details(id):
    remark_deatils = Request.query.filter_by(id=id).first()
    return render_template("request_details.html", requests=remark_deatils)


# Admin Chart: Professional Status Breakdown
@views.route('/prof_status/chart')
def prof_chart():
    # Fetch data from the database
    approved_count = Professional.query.filter_by(status='approved').count()
    rejected_count = Professional.query.filter_by(status='rejected').count()
    pending_count = Professional.query.filter_by(status='pending').count()
    block_count = Professional.query.filter_by(status='blocked').count()

    fig_prof, ax_prof = plt.subplots()
    categories = ["Approved", "Blocked", "Pending", "Rejected"]
    counts = [approved_count, block_count, pending_count, rejected_count]
    ax_prof.bar(categories, counts, color=["lightgreen", "red", "yellow", "blue"])

    ax_prof.set_xlabel('Status')
    ax_prof.set_ylabel('Count')
    ax_prof.set_title('Professional Status')
    ax_prof.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    img_prof = io.BytesIO()
    plt.savefig(img_prof, format='png')
    plt.close(fig_prof)
    img_prof.seek(0)

    response = Response(img_prof.getvalue(), mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store'  # Prevent caching issues
    img_prof.close()
    return response


# Admin Chart: Customer Status Breakdown
@views.route("/cust_status/chart")
def cust_chart():
    # Fetch data from the database
    active_count = User.query.filter_by(status='active').count()
    block_count = User.query.filter_by(status='blocked').count()

    fig_cust, ax_cust = plt.subplots()
    categories = ["Active", "Blocked"]
    counts = [active_count, block_count]
    ax_cust.bar(categories, counts, color=["lightgreen", "red"])

    ax_cust.set_xlabel('Status')
    ax_cust.set_ylabel('Count')
    ax_cust.set_title('Customer Status')
    ax_cust.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    img_cust = io.BytesIO()
    plt.savefig(img_cust, format='png')
    plt.close(fig_cust)
    img_cust.seek(0)

    response = Response(img_cust.getvalue(), mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store'
    img_cust.close()
    return response


# Admin Chart: Service Request Status Breakdown
@views.route("/request_status/chart")
def request_chart():
    # Fetch data from the database
    request_count = Request.query.filter_by(service_status='pending').count()
    accept_count = Request.query.filter_by(service_status='accepted').count()
    rejected_count = Request.query.filter_by(service_status='rejected').count()
    closed_count = Request.query.filter_by(service_status='closed').count()

    fig_req, ax_req = plt.subplots()
    categories = ["Requested", "Accepted", "Rejected", "Closed"]
    counts = [request_count, accept_count, rejected_count, closed_count]
    ax_req.bar(categories, counts, color=["yellow", "lightgreen", "red", "blue"])

    ax_req.set_xlabel('Status')
    ax_req.set_ylabel('Count')
    ax_req.set_title('Request Status')
    ax_req.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    img_req = io.BytesIO()
    plt.savefig(img_req, format='png')
    plt.close(fig_req)
    img_req.seek(0)

    response = Response(img_req.getvalue(), mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store'
    img_req.close()
    return response


# Admin Chart: Average Rating by Service
@views.route("/average_rating/chart")
def average_rating_chart():
    # Get all ratings grouped by service
    ratings = Request.query.all()
    service_ratings = {}

    # Calculate total ratings and counts for each service
    for r in ratings:
        if r.service not in service_ratings:
            service_ratings[r.service] = {'total_rating': 0, 'count': 0}
        
        if r.rating is not None:  # Check if the rating is not None
            service_ratings[r.service]['total_rating'] += r.rating
            service_ratings[r.service]['count'] += 1

    services = []
    avg_ratings = []

    for service, data in service_ratings.items():
        avg_rating = data['total_rating'] / data['count'] if data['count'] > 0 else 0
        services.append(service.service)
        avg_ratings.append(avg_rating)

    # Check if services and avg_ratings have values
    if not services or not avg_ratings:
        return "No data available", 404

    fig_rating, ax_rating = plt.subplots()
    colors = plt.cm.viridis(np.linspace(0, 1, len(services)))
    ax_rating.barh(services, avg_ratings, color=colors)
    ax_rating.set_xlim(0, 5)
    ax_rating.set_xlabel('Average Rating')
    ax_rating.set_ylabel('Services')
    ax_rating.set_title('Average Rating by Service')

    plt.yticks(rotation=0)  # Ensure y-ticks are horizontal
    plt.subplots_adjust(left=0.2)  # Adjust left margin
    plt.tight_layout()  # Automatically adjust layout

    img_rating = io.BytesIO()
    plt.savefig(img_rating, format='png')
    plt.close(fig_rating)
    img_rating.seek(0)

    response = Response(img_rating.getvalue(), mimetype='image/png')
    response.headers['Cache-Control'] = 'no-store'
    img_rating.close()
    return response



# Professional Chart: Professional's Rating Distribution
@views.route('/rating/chart')
def rating_chart():
    prof_id = current_user.id
    ratings = Request.query.filter_by(professional_id=prof_id).all()

    count_1 = len([r for r in ratings if r.rating == 1])
    count_2 = len([r for r in ratings if r.rating == 2])
    count_3 = len([r for r in ratings if r.rating == 3])
    count_4 = len([r for r in ratings if r.rating == 4])
    count_5 = len([r for r in ratings if r.rating == 5])

    # Generate the bar chart for Rating Distribution
    fig1, ax1 = plt.subplots()
    categories = ["1", "2", "3", "4", "5"]
    counts = [count_1, count_2, count_3, count_4, count_5]
    ax1.bar(categories, counts, color=["red","orange", "yellow", "lightgreen", "green"])

    ax1.set_xlabel('Rating')
    ax1.set_ylabel('Count')
    ax1.set_title('Rating Status')
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))


    # Save the figure to a BytesIO object
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plt.close(fig1)

    return Response(img1.getvalue(), mimetype='image/png')



# Professional Chart: Service Request Status Breakdown for a Professional
@views.route('/service/chart')
def service_chart():
    prof_id = current_user.id
    service = Request.query.filter_by(professional_id=prof_id).all()

    count_1 = len([r for r in service if r.service_status == "pending"])
    count_2 = len([r for r in service if r.service_status == "accepted"])
    count_3 = len([r for r in service if r.service_status == "rejected"])
    count_4 = len([r for r in service if r.service_status == "closed"])


    # Generate the bar chart for Service Status
    fig1, ax1 = plt.subplots()
    categories = ["Pending", "Accepted", "Rejected", "Closed"]
    counts = [count_1, count_2, count_3, count_4]
    ax1.bar(categories, counts, color=["blue", "lightgreen", "red", "yellow"])

    ax1.set_xlabel('Service Status')
    ax1.set_ylabel('Count')
    ax1.set_title('Service Requests Status')
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))


    # Save the figure to a BytesIO object
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plt.close(fig1)

    return Response(img1.getvalue(), mimetype='image/png')




# Customer Chart: Service Request Status Breakdown for a Customer
@views.route("/service_requested/chart")
def service_requested_chart():
    user_id = current_user.id
    service = Request.query.filter_by(customer_id=user_id).all()

    count_1 = len([r for r in service if r.service_status == "pending"])
    count_2 = len([r for r in service if r.service_status == "accepted"])
    count_3 = len([r for r in service if r.service_status == "rejected"])
    count_4 = len([r for r in service if r.service_status == "closed"])


    # Generate the bar chart for Service Status
    fig1, ax1 = plt.subplots()
    categories = ["Pending", "Accepted", "Rejected", "Closed"]
    counts = [count_1, count_2, count_3, count_4]
    ax1.bar(categories, counts, color=["blue", "lightgreen", "red", "yellow"])

    ax1.set_xlabel('Service Status')
    ax1.set_ylabel('Count')
    ax1.set_title('Service Requests Status')
    ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))


    # Save the figure to a BytesIO object
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plt.close(fig1)

    return Response(img1.getvalue(), mimetype='image/png')