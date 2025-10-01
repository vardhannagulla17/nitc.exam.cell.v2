# NIT Calicut Exam Cell Application

A comprehensive Flask-based web application for managing exam attendance sheets at NIT Calicut. The application supports multiple semesters, academic years, and exam types with professional NITC-formatted attendance sheet generation.

## 🎯 Features

### 📋 Core Functionality
- **Multi-Semester Support**: Separate databases for each academic session
- **User Authentication**: Secure login system with session management
- **Excel Data Import**: Upload and process student data from Excel files
- **Professional Attendance Sheets**: Generate NITC-compliant HTML attendance sheets
- **Preview & Download**: Preview sheets before downloading, bulk ZIP downloads
- **Smart Sorting**: Students sorted by department and roll number

### 🎓 Academic Configuration
- **Academic Years**: 2024-25, 2025-26, 2026-27, 2027-28
- **Semesters**: Monsoon, Winter
- **Degree Levels**: UG (Undergraduate), PG (Postgraduate)
- **Exam Types**: Mid Semester, End Semester

### 📄 Attendance Sheet Features
- Official NITC header and branding
- Department of Mechanical Engineering format
- Bio break tracking column
- Additional answer sheets tracking
- Invigilator signature sections
- Answer books details (Main/Additional)
- Multi-page support (60 students per page)
- Print-ready HTML format

## 🚀 Installation

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Required Packages
```bash
pip install flask pandas openpyxl werkzeug
```

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nitc-exam-cell-app.git
   cd nitc-exam-cell-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## 📱 Usage

### 1. Login
- **Username**: `admin`
- **Password**: `admin123`
- (Change these credentials in production)

### 2. Upload Student Data
1. Navigate to the Upload tile
2. Select academic year, semester, degree level, and exam type
3. Upload Excel file with student data
4. Data is stored in semester-specific databases

### 3. Generate Attendance Sheets
1. Go to Download section
2. Select the semester configuration
3. Choose specific course or download all courses
4. Preview sheets before downloading
5. Download individual sheets or bulk ZIP files

## 📊 Database Schema

### Main Database (`exam_cell.db`)
- **users**: User authentication data
- **semesters**: Academic session configurations

### Semester-Specific Databases
- **students**: Complete student information for each semester
- Format: `students_YYYY_YY_semester_degree_examtype.db`

## 📁 Project Structure

```
ExamCellApp/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── exam_cell.db                   # Main SQLite database
├── static/
│   └── style.css                  # CSS styling
├── templates/
│   ├── base.html                  # Base template
│   ├── login.html                 # Login page
│   ├── dashboard.html             # Main dashboard
│   ├── upload.html                # File upload page
│   └── download.html              # Download/preview page
├── uploads/                       # Uploaded Excel files
├── downloads/                     # Generated attendance sheets
└── attendance_sheet_template.html # Sample format reference
```

## 📋 Excel File Format

Your Excel file should contain these columns:
- **RollNo**: Student roll number
- **NameasPerXStd**: Student name
- **EmailId**: Student email
- **CourseCode**: Course code (e.g., MA6001E)
- **CourseTitle**: Full course title
- **Credits**: Course credits
- **MainInstructor**: Instructor name
- **ProgramName**: Program/degree name
- **TimetableBatch**: Batch information
- **SlotCode**: Time slot code
- **PrimaryMail**: Primary instructor email
- **CourseCategoryCode**: Course category

## 🎨 Attendance Sheet Format

### Header Information
- National Institute of Technology Calicut
- Department of Mechanical Engineering
- Statement of Answer Books and Bio breaks Details
- Academic year, semester, exam type automatically filled

### Student Table
| Sl. No. | Roll No. | Student Name | Details of Bio Break | No. of Additional Sheets |
|---------|----------|--------------|---------------------|---------------------------|
| 1       | M250274ME| ARON THOMAS  |                     |                           |

### Administrative Sections
- **Invigilator Signatures**: Table for 2 invigilators with date
- **Answer Books Details**: Tracking for received, used, and balance sheets

## 🔧 Configuration

### Default Settings
- **Rows per page**: 60 students
- **File upload limit**: 16MB
- **Supported formats**: .xlsx, .xls
- **Database**: SQLite

### Security Features
- Password hashing using Werkzeug
- Session management
- File upload validation
- CSRF protection

## 🔄 Student Sorting Algorithm

Students are sorted using a two-level approach:
1. **Primary sort**: Department code (last 2 letters of roll number)
2. **Secondary sort**: Numeric part within department

Example:
- M250274ME (ME dept, 250274)
- M250313ME (ME dept, 250313)
- M250824ME (ME dept, 250824)

## 🌐 API Endpoints

- `GET /` - Redirect to login/dashboard
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /logout` - Logout user
- `GET /dashboard` - Main dashboard with statistics
- `GET /upload` - Upload form
- `POST /upload` - Process file upload
- `GET /download` - Download form with semester selection
- `POST /download` - Generate/preview/download attendance sheets

## 🎯 Advanced Features

### Preview Functionality
- View attendance sheets in browser before downloading
- No file generation for previews
- New window/tab opens with formatted sheet

### Bulk Download
- Download all courses for a semester as ZIP file
- Automatic file naming with semester information
- Progress indication during generation

### Multi-Semester Management
- Each semester maintains separate database
- Cross-semester statistics on dashboard
- Easy switching between semesters

## 🛠️ Development

### Adding New Academic Years
Update the dropdown options in `templates/upload.html`:
```html
<option value="2028-29">2028-29</option>
```

### Customizing Attendance Format
Modify the `generate_attendance_sheet()` function in `app.py` to change:
- Page layout
- Header information
- Table structure
- Styling

### Database Migration
To add new fields to student records:
1. Update the database schema in `init_db()` and `create_semester_db()`
2. Modify the Excel import logic in `load_excel_to_db()`
3. Update attendance sheet generation accordingly

## 🔒 Security Considerations

### Production Deployment
1. Change default admin credentials
2. Use environment variables for sensitive data
3. Implement HTTPS
4. Add rate limiting
5. Use production WSGI server (e.g., Gunicorn)

### Example Production Configuration
```python
app.secret_key = os.environ.get('SECRET_KEY', 'your-production-secret-key')
```

## 🐛 Troubleshooting

### Common Issues
1. **Database not found**: Run the app once to initialize databases
2. **Excel import fails**: Check column names match expected format
3. **Preview not working**: Ensure popup blockers are disabled
4. **ZIP download issues**: Check download folder permissions

### Debug Mode
Set `debug=True` in `app.run()` for development debugging.

## 📈 Future Enhancements

- [ ] User role management (admin, faculty, staff)
- [ ] Email notifications for attendance sheet generation
- [ ] PDF export option
- [ ] Automated backup system
- [ ] REST API for mobile app integration
- [ ] Audit logging for all operations
- [ ] Integration with institute ERP system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Your Name - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- National Institute of Technology Calicut
- Department of Mechanical Engineering
- Flask framework and community
- Contributors and testers

## 📞 Support

For support and queries:
- Create an issue on GitHub
- Contact: your.email@nitc.ac.in

---

**Made with ❤️ for NIT Calicut**
