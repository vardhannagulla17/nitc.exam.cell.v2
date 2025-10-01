# API Documentation

## Overview
This document describes the API endpoints available in the NITC Exam Cell Attendance Management System.

## Authentication
Most endpoints require user authentication. Users must log in through the `/login` endpoint to receive a session cookie.

## Endpoints

### Authentication Endpoints

#### POST /login
Log in to the system.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
- Success: Redirect to dashboard
- Error: Flash message with error details

#### GET /logout
Log out of the system.

**Response:**
- Redirect to login page

### Dashboard Endpoints

#### GET /dashboard
Display the main dashboard with statistics and uploaded files.

**Access:** Authenticated users
**Admin Features:** View uploaded files, delete files

### File Management Endpoints

#### GET /upload
Display the file upload form.

**Access:** Admin users only

#### POST /upload
Upload an Excel file with student enrollment data.

**Request Body (multipart/form-data):**
- `file`: Excel file (.xlsx or .xls)
- `academic_year`: Academic year (e.g., "2024-25")
- `semester_type`: Semester type ("monsoon" or "winter")
- `sheet_type`: Sheet type ("UG", "PG", "PhD", or "combined")
- `exam_type`: Exam type ("midsem" or "endsem")

**Access:** Admin users only

#### GET /delete_file/<filename>
Delete an uploaded file and associated semester data.

**Access:** Admin users only

### Attendance Sheet Endpoints

#### GET /download
Display the attendance sheet download interface.

**Query Parameters:**
- `program_level`: Filter by program level (UG, PG, PhD)
- `semester_id`: Filter by semester ID

#### POST /download
Generate attendance sheets.

**Request Body:**
- `action`: Action to perform ("download", "download_simple", "preview", "preview_simple", "download_all")
- `program_level`: Program level (UG, PG, PhD)
- `semester_id`: Semester ID
- `course_code`: Course code (required for individual downloads)
- `exam_date`: Exam date (required)

**Actions:**
- `download`: Generate detailed attendance sheet for a course
- `download_simple`: Generate simple attendance sheet for a course
- `preview`: Preview detailed attendance sheet
- `preview_simple`: Preview simple attendance sheet
- `download_all`: Generate all attendance sheets as ZIP

## Data Models

### User
```json
{
    "id": "integer",
    "username": "string",
    "role": "string" // "admin" or "staff"
}
```

### Semester
```json
{
    "id": "integer",
    "academic_year": "string",
    "semester_type": "string",
    "degree_level": "string",
    "exam_type": "string",
    "db_name": "string"
}
```

### Student
```json
{
    "id": "integer",
    "roll_no": "string",
    "name": "string",
    "email_id": "string",
    "student_sess": "string",
    "course_code": "string",
    "credits": "integer",
    "course_title": "string",
    "program_name": "string",
    "timetable_batch": "string",
    "slot_code": "string",
    "main_instructor": "string",
    "primary_mail": "string",
    "course_category_code": "string"
}
```

## Error Handling

The API uses Flask's flash messaging system for user feedback:

- `success`: Operation completed successfully
- `error`: Operation failed with error details
- `info`: Informational messages

## File Formats

### Excel File Requirements
Uploaded Excel files should contain the following columns:
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

### Generated Files
- **Detailed Attendance Sheet**: HTML file with bio-breaks tracking
- **Simple Attendance Sheet**: HTML file with signature column only
- **ZIP Archive**: Contains all attendance sheets organized by program and course
