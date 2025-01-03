# Household Services Application

### 🌟 Overview
The app aims to simplify household service management, offering a secure, user-friendly interface for customers to find verified professionals, manage service requests, and provide feedback. Admins maintain quality control, approving professionals and overseeing platform operations.

---

## 🛠️ Frameworks Used
The application uses:
- **Flask** for server logic
- **Jinja2 templates with Bootstrap** for responsive UI
- **SQLite** as the lightweight, compatible database

All functionality has been thoroughly tested in a local development environment.

---

## 👥 User Roles & Permissions
- **Admin:** Manages user and service data, approves professionals, and enforces platform rules.
- **Service Professional:** Registers, manages profiles, accepts/rejects service requests, and completes service transactions.
- **Customer:** Registers to request services, search by service or location, and leave feedback.

---

## 📂 Database Schema
- **Admin Model:** Manages superuser accounts with fields like id, email, and password.
- **User Model:** Stores customer information and status.
- **Professional Model:** Holds professional profile data, service expertise, and average ratings.
- **Service Model:** Defines service categories with descriptions and base prices.
- **Request Model:** Tracks each service request’s status, customer remarks, and ratings.

---

## 🔑 Core Functionalities
- **Authentication and Authorization:** Enforced with Flask-Login, offering role-based access and session management for Admin, Service Professional, and Customer roles.
- **Admin Dashboard:** Allows the Admin to manage services, approve professionals, and review user activities.
- **Service Management:** Admin can add, edit, or delete service categories with essential details like price and description.
- **Service Request Management:** Customers submit requests; professionals can accept, reject, or close them after completion.
- **Search Feature:** Customers search by service name or location; Admins search professionals by status.

---

## 🌀 Application Workflow
1. **Login & Role Redirection:** Users log in and are redirected to dashboards based on their role.
2. **Service Request:** Customers select services, make requests, and post feedback after completion.
3. **Feedback Loop:** Professionals receive feedback to improve visibility.

---

## 📈 Conclusion
This Household Services Application fulfills its goal of connecting customers with trusted service providers, with future improvements like more robust authentication and payment integration planned for enhanced user experience.
