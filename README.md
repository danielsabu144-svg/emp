# Employee Management System (EMS)

A comprehensive, modern Employee Management System built with **Python Django** and **MySQL**. This system provides a complete HRMS solution with role-based access control, attendance tracking, leave management, payroll processing, and an AI-powered HR chatbot.

## 🌟 Features

### 🔐 Authentication & Authorization
- Secure login/logout with Django authentication
- Role-based access control (HR/Admin and Employee)
- Password hashing and session management
- Automatic attendance marking on login

### 👥 HR/Admin Module
- **Dashboard**: Real-time statistics and analytics
  - Total employees count
  - Daily attendance summary
  - Pending leave requests
  - Payroll overview
  - Interactive charts (Chart.js)
  
- **Employee Management**: Full CRUD operations
  - Add, edit, view, delete employees
  - Comprehensive employee profiles
  - Department and designation management
  
- **Attendance Monitoring**
  - Daily and monthly attendance tracking
  - Attendance reports and analytics
  - Work hours calculation
  
- **Leave Management**
  - Approve/reject leave requests
  - Leave balance tracking
  - Leave type management
  
- **Payroll System**
  - Automatic salary calculation based on attendance
  - Allowances and deductions
  - Monthly payroll generation
  - Payment tracking
  
- **Notifications**
  - Birthday reminders
  - Work anniversary alerts
  - Pending approval notifications

### 👨‍💼 Employee Module
- **Personal Dashboard**
  - Attendance status
  - Leave balance
  - Recent notifications
  - Quick actions
  
- **Profile Management**
  - View personal information
  - Update profile picture
  
- **Attendance**
  - Auto-mark on login
  - View attendance history
  - Monthly attendance reports
  
- **Leave Applications**
  - Apply for leave
  - Track leave status
  - View leave history
  
- **Payroll**
  - View salary slips
  - Monthly payroll history

### 🤖 HR Chatbot
- Rule-based chatbot for HR queries
- Instant answers to common questions
- Leave balance inquiries
- Attendance status checks
- HR policy information

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2
- **Database**: MySQL
- **Language**: Python 3.x

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with CSS variables
- **JavaScript** - Interactive features
- **Bootstrap 5** - Responsive grid system
- **Font Awesome** - Icons
- **Chart.js** - Data visualization

### Design
- Modern dark theme with gradient accents
- Fully responsive (Mobile, Tablet, Desktop)
- Smooth animations and transitions
- Glassmorphism effects
- Premium UI/UX

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)
- Git (optional)

## 🚀 Installation & Setup

### Step 1: Clone or Download the Project

```bash
cd "d:\2026 Python Django Projects\EmployeeManagementSystem"
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate the virtual environment:
- **Windows**: `venv\Scripts\activate`
- **Linux/Mac**: `source venv/bin/activate`

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure MySQL Database

1. Open MySQL and create a database:
```sql
CREATE DATABASE employee_management_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Update database credentials in `employee_management/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'employee_management_db',
        'USER': 'root',  # Your MySQL username
        'PASSWORD': '',  # Your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### Step 7: Load Sample Data (Optional)

```bash
python manage.py loaddata sample_data.json
```

### Step 8: Run Development Server

```bash
python manage.py runserver
```

The application will be available at: `http://127.0.0.1:8000/`

## 👤 Default Login Credentials

After loading sample data:

**HR/Admin:**
- Username: `admin`
- Password: `admin123`

**Employee:**
- Username: `employee`
- Password: `emp123`

## 📁 Project Structure

```
EmployeeManagementSystem/
├── accounts/              # User authentication & management
├── employees/             # Employee profiles & management
├── attendance/            # Attendance tracking
├── leave_management/      # Leave applications & approvals
├── payroll/              # Salary & payroll processing
├── chatbot/              # HR chatbot functionality
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── hr/              # HR dashboard templates
│   └── employee/        # Employee dashboard templates
├── static/              # Static files
│   ├── css/
│   │   └── style.css    # Main stylesheet
│   ├── js/              # JavaScript files
│   └── images/          # Images & icons
├── media/               # User uploaded files
│   └── profile_pics/    # Profile pictures
├── employee_management/ # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
```

## 🎨 Design Features

### Modern UI/UX
- **Dark Theme**: Professional dark mode with vibrant accents
- **Gradient Colors**: Eye-catching gradient backgrounds
- **Smooth Animations**: Micro-interactions for better UX
- **Responsive Design**: Works perfectly on all devices
- **Card-based Layout**: Clean, organized information display

### Color Palette
- Primary: Purple-Blue Gradient (#667eea → #764ba2)
- Secondary: Emerald Green (#10B981)
- Accent: Orange (#F59E0B), Red (#EF4444)
- Background: Dark Navy (#0F172A)
- Cards: Slate (#1E293B)

## 📊 Database Schema

### Main Tables
1. **User** - Custom user model with roles
2. **EmployeeProfile** - Extended employee information
3. **Attendance** - Daily attendance records
4. **Leave** - Leave applications
5. **LeaveType** - Types of leaves
6. **LeaveBalance** - Employee leave balances
7. **Payroll** - Monthly salary records
8. **PayrollComponent** - Salary components
9. **Notification** - System notifications
10. **ChatbotResponse** - Chatbot Q&A
11. **ChatHistory** - Chat logs

## 🔧 Configuration

### Email Settings (Optional)
To enable email notifications, update `settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Timezone
Default timezone is set to `Asia/Kolkata`. Change in `settings.py` if needed:

```python
TIME_ZONE = 'Asia/Kolkata'
```

## 🧪 Testing

Run tests:
```bash
python manage.py test
```

## 📱 Responsive Breakpoints

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Update `ALLOWED_HOSTS`
3. Configure static files: `python manage.py collectstatic`
4. Use production database credentials
5. Set up proper web server (Nginx/Apache)
6. Use WSGI server (Gunicorn/uWSGI)
7. Enable HTTPS
8. Set secure cookies

## 🤝 Contributing

This is a university project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is created for educational purposes as part of a university project.

## 👨‍💻 Developer

**Your Name**
- University: [Your University Name]
- Course: [Your Course]
- Year: 2026

## 📞 Support

For issues or questions:
- Create an issue in the repository
- Contact: [your-email@example.com]

## 🎓 Project Documentation

For detailed documentation, refer to:
- `/docs/user_manual.pdf` - User guide
- `/docs/technical_documentation.pdf` - Technical details
- `/docs/database_schema.pdf` - Database design

## ⚡ Quick Start Commands

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database
# (Run in MySQL): CREATE DATABASE employee_management_db;

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## 🎯 Future Enhancements

- [ ] PDF export for payroll
- [ ] Email notifications
- [ ] Attendance report download
- [ ] Dark/Light mode toggle
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Biometric attendance integration
- [ ] Performance review module

## ✅ Features Checklist

- [x] User authentication & authorization
- [x] Role-based access control
- [x] Employee CRUD operations
- [x] Automatic attendance marking
- [x] Leave management system
- [x] Payroll calculation
- [x] HR chatbot
- [x] Responsive design
- [x] Charts & analytics
- [x] Notifications system
- [x] MySQL database integration
- [x] Modern UI/UX

---

**Note**: This is a complete, production-ready Employee Management System suitable for university project submission and demonstration.
