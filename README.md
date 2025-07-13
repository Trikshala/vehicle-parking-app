# vehicle-parking-app

A dummy web application that allows users to search and book available parking spots for their 4-wheelers in different locations.
This system supports two types of users: **Admin** and **Regular User**, each with dedicated features and dashboards.

---

## 👥 User Roles & Capabilities

### 🔐 Regular User
- Register and log in to their own account
- Search for parking lots by location
- Book available parking spots by providing vehicle model and estimated duration
- View personal parking history with check-in/check-out times and cost breakdown
- Access user-friendly analytics through bar graphs and pie charts

### 🛠️ Admin
- Create, update, and delete parking lots with full details (location, cost/hr, max spots)
- Change pricing or maximum spot count for existing lots
- View all registered users
- Access user-specific reservation history and status
- Use advanced search: search users by ID or lots by location
- View analytics and dashboard insights via charts

---

## 📊 Extras & Highlights
- Reservation pricing that adapts to time parked
- Deleted lots are archived to preserve reservation history
- Clean, role-specific UI with contextual feedback
- Authentication & authorization handled with Flask-Login
- Visual analytics using chart.js (bar & pie charts)

---

## 💡 Note
This is a *dummy app* meant to simulate the functionality of a real-world smart parking system.  
Actual payment integration, real-time lot tracking, or IoT integration is *not* implemented.

---

## 🧪 Tech Stack
- Python + Flask
- SQLite (migratable to MySQL/PostgreSQL)
- SQLAlchemy ORM
- WTForms + Flask-WTF
- HTML/CSS (Jinja templates + Bootstrap 5)
- Flask-Login & Flask-Bcrypt

---

## How to Run - Installation and Setup
1. Clone the repository 
-  git clone [vehicle-parking-app](https://github.com/23f3002986/vehicle-parking-app.git)
-  cd vehicle-parking-app

2. Set up virtual environment:
-  python -m venv venv
-  venv\Scripts\activate # On Windows
-  source venv/bin/activate # On macOS/Linux

3. Install dependencies:
-  pip install -r requirements.txt

4. Run the app:
-  python run.py 
> App runs at: http://127.0.0.1:5000/

---

## 🗃️ Database Info

- Uses *SQLite* for this version (project requirement)
- Models include: `User`, `ParkingLot`, `ParkingSpot`, `Reservation`
- Foreign key constraints with cascade + archive fields to preserve deleted lot history
- Foreign key enforcement enabled using `PRAGMA foreign_keys = ON` in `__init__.py`

---

## 📖 Usage

- **Users** can register, search for lots, book spots, and check reservation history.
- **Admins** can add/delete lots, manage spot capacity, and monitor reservations.

> Even deleted lots' reservation data remains accessible, shown with "(archived)" labels.

---

## 🚧 Limitations & Future Plans

- Currently uses SQLite – future plans to migrate to MySQL/PostgreSQL
- No payment gateway or OTP verification yet
- UI is powered by Bootstrap 5 – may be further enhanced with JavaScript frameworks

---

## 👩‍💻 Author

THODUPUNURI TRIKSHALA GOUD  
Final Year CSE Student | St. Martin's Engineering College  
IITM Data Science Online Diploma Program  