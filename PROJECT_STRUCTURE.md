# NITC Exam Cell v2 - Project Structure

## Directory Organization

```
nitc.exam.cell.v2/
│
├── api/                        # Vercel serverless functions
│   └── index.py               # Entry point for Vercel deployment
│
├── app/                        # Application core modules
│   ├── __init__.py
│   ├── attendance.py          # Attendance sheet generation logic
│   ├── database.py            # Database connection abstraction
│   └── models.py              # Data models and database operations
│
├── helpers/                    # Utility functions
│   ├── __init__.py
│   ├── database_utils.py      # Database helper functions
│   ├── file_utils.py          # File handling utilities
│   └── utils.py               # General utilities (sorting, etc.)
│
├── static/                     # Static assets (CSS, images, JS)
│   ├── css/                   # Stylesheets
│   │   ├── base.css
│   │   ├── components.css
│   │   ├── dashboard.css
│   │   ├── forms.css
│   │   ├── layout.css
│   │   ├── login.css
│   │   └── utils.css
│   └── style.css              # Main stylesheet
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html              # Base template
│   ├── dashboard.html         # Dashboard page
│   ├── download.html          # Attendance generation page
│   ├── error.html             # Error page
│   ├── login.html             # Login page
│   ├── upload.html            # File upload page
│   └── absentee.html          # Absentee sheet page
│
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   └── DEPLOYMENT.md          # Deployment guide
│
├── uploads/                    # Uploaded Excel files (gitignored)
├── downloads/                  # Generated attendance sheets (gitignored)
├── logs/                       # Application logs (gitignored)
│
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── run.py                      # Local development runner
├── supabase_client.py         # Supabase client initialization
├── supabase_schema.sql        # Database schema for Supabase
│
├── requirements.txt            # Python dependencies
├── runtime.txt                # Python version for deployment
├── vercel.json                # Vercel configuration
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose configuration
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── .vercelignore              # Vercel ignore rules
├── .dockerignore              # Docker ignore rules
│
└── README.md                  # Project documentation
```

## Key Components

### Backend
- **app.py**: Main Flask application with all routes
- **app/models.py**: Database models and CRUD operations
- **app/attendance.py**: Attendance sheet generation (HTML)
- **app/database.py**: Database connection handler (Supabase/SQLite)

### Frontend
- **templates/**: Jinja2 templates for all pages
- **static/css/**: Modular CSS files for styling

### Deployment
- **api/index.py**: Vercel serverless function entry point
- **vercel.json**: Vercel deployment configuration
- **supabase_schema.sql**: Database schema for Supabase PostgreSQL

### Utilities
- **helpers/utils.py**: Sorting and utility functions
- **supabase_client.py**: Supabase client singleton

## Environment Configuration

### Local Development
- Uses SQLite databases
- Stores files in local filesystem
- `.env` file for configuration

### Production (Vercel)
- Uses Supabase PostgreSQL
- Stores files in Supabase Storage
- Environment variables set in Vercel dashboard

## Key Features

1. **Dual Database Support**: Automatic switching between SQLite (local) and Supabase (production)
2. **Smart Excel Import**: Flexible column name detection
3. **Program-Level Filtering**: Separate UG/PG/PhD data handling
4. **Attendance Sheet Generation**: NITC format with bio-breaks
5. **Absentee Sheet Management**: Track absent students
6. **Admin Dashboard**: Database usage statistics and file management

## Database Schema

### Tables
- **users**: Admin and staff accounts
- **semesters**: Academic semester information
- **students**: Student enrollment data per semester

See `supabase_schema.sql` for complete schema definition.
