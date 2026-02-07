# NITC Exam Cell Attendance Management System

A Flask-based web application for managing student attendance sheets for examinations at the National Institute of Technology Calicut.

## Features

- **User Authentication**: Admin and staff user roles with email-based OTP verification
- **Email-based Registration**: Staff can self-register using @nitc.ac.in email with OTP verification
- **Exam Timetable Management**: Upload exam timetables (Excel/PDF) for auto-fill of exam dates
- **Excel File Upload**: Upload student enrollment data from Excel files
- **Attendance Sheet Generation**: Generate detailed attendance sheets (includes signature, bio-break and additional sheets columns)
- **Bulk Downloads**: Download all attendance sheets as organized ZIP files
- **Program-wise Organization**: Separate folders for UG, PG, and PhD programs
- **Semester Management**: Handle multiple semesters and examination types

## Project Structure

```
pran-cell/
├── app/                    # Main application package
│   ├── __init__.py        # Application factory
│   ├── models.py          # Database models and operations
│   ├── routes.py          # Flask routes and views
│   ├── attendance.py      # Attendance sheet generation
│   └── utils.py           # Utility functions
├── templates/             # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── download.html
│   ├── login.html
│   └── upload.html
├── static/                # Static files (CSS, JS)
│   └── style.css
├── uploads/               # Uploaded Excel files
├── downloads/             # Generated attendance sheets
│   ├── UG/
│   ├── PG/
│   └── PhD/
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pran-cell
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```

4. **Access the application**
   Open your browser and go to `http://127.0.0.1:5000`

## Default Login Credentials

- **Admin**: username: `admin`, password: `admin123`
- **Staff**: username: `staff1`, password: `staff123`

## Usage

1. **Login** with your credentials
2. **Upload Excel files** containing student enrollment data (Admin only)
3. **Select semester and program** for attendance sheet generation
4. **Generate attendance sheets** in detailed format
5. **Download individual sheets** or **bulk download** all sheets as ZIP

## File Formats

The application accepts Excel files (.xlsx, .xls) with the following expected columns:
- RollNo
- NameasPerXStd
- EmailId
- studentsess
- CourseCode
- Credits
- CourseTitle
- ProgramName
- TimetableBatch
- SlotCode
- MainInstructor
- PrimaryMail
- CourseCategoryCode

## Environment Variables

For OTP-based email verification, configure the following environment variables:

```bash
# SMTP Configuration for OTP emails
SMTP_SERVER=smtp.gmail.com       # SMTP server address
SMTP_PORT=587                    # SMTP port (587 for TLS)
SMTP_USER=your-email@gmail.com   # SMTP username/email
SMTP_PASSWORD=your-app-password  # SMTP password or app password
SMTP_FROM=noreply@nitc.ac.in     # From email address
```

**Note**: For Gmail, you need to use an App Password (not your regular password). Enable 2FA and generate an App Password from Google Account settings.

## Development

This application uses the Flask application factory pattern for better organization and scalability.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
