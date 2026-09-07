import pandas as pd
import re

from database.db_setup import create_semester_db, get_semester_db_name
from database.repository import replace_students_for_semester, upsert_semester_and_clear_students
from helpers.utils import get_program_level


def detect_excel_column(df, possible_names):
    def normalize(value):
        return re.sub(r'[^a-z0-9]', '', str(value).strip().lower())

    df_columns_lower = {normalize(col): col for col in df.columns}
    for name in possible_names:
        name_lower = normalize(name)
        if name_lower in df_columns_lower:
            return df_columns_lower[name_lower]
        for col_lower, col_original in df_columns_lower.items():
            if name_lower in col_lower or col_lower in name_lower:
                return col_original
    return None


def _find_header_row(file_source, sheet_name):
    preview = pd.read_excel(file_source, sheet_name=sheet_name, engine='openpyxl', header=None, nrows=20)
    header_markers = (
        'rollno',
        'rollnumber',
        'registrationno',
        'registrationnumber',
        'regno',
        'studentid',
        'studentname',
        'coursecode',
    )
    for index, row in preview.iterrows():
        values = {
            re.sub(r'[^a-z0-9]', '', str(value).strip().lower())
            for value in row.tolist()
            if pd.notna(value)
        }
        if any(marker in value for marker in header_markers for value in values):
            return int(index)
    return None


def _read_student_workbook(file_source):
    workbook = pd.ExcelFile(file_source, engine='openpyxl')
    frames = []
    for sheet_name in workbook.sheet_names:
        header_row = _find_header_row(file_source, sheet_name)
        if header_row is None:
            continue
        frame = pd.read_excel(
            file_source,
            sheet_name=sheet_name,
            engine='openpyxl',
            header=header_row,
        )
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def _text_value(value):
    if pd.isna(value):
        return ''
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _integer_value(value):
    if pd.isna(value) or str(value).strip() == '':
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _normalize_students(df, columns):
    students_data = []
    for _, row in df.iterrows():
        students_data.append(
            {
                'roll_no': _text_value(row.get(columns['roll'], '')) if columns['roll'] else '',
                'name': _text_value(row.get(columns['name'], '')) if columns['name'] else '',
                'email_id': _text_value(row.get(columns['email'], '')) if columns['email'] else '',
                'student_sess': _text_value(row.get(columns['sess'], '')) if columns['sess'] else '',
                'course_code': _text_value(row.get(columns['course_code'], '')) if columns['course_code'] else '',
                'credits': _integer_value(row.get(columns['credits'], 0)) if columns['credits'] else 0,
                'course_title': _text_value(row.get(columns['course_title'], '')) if columns['course_title'] else '',
                'program_name': _text_value(row.get(columns['program'], '')) if columns['program'] else '',
                'timetable_batch': _text_value(row.get(columns['batch'], '')) if columns['batch'] else '',
                'slot_code': _text_value(row.get(columns['slot'], '')) if columns['slot'] else '',
                'main_instructor': _text_value(row.get(columns['instructor'], '')) if columns['instructor'] else '',
                'primary_mail': _text_value(row.get(columns['primary_mail'], '')) if columns['primary_mail'] else '',
                'course_category_code': _text_value(row.get(columns['category'], '')) if columns['category'] else '',
                'section': _text_value(row.get(columns['section'], '')) if columns['section'] else '',
            }
        )
    return students_data


def load_excel_to_db(file_source, academic_year, semester_type, sheet_type, exam_type):
    try:
        if hasattr(file_source, 'seek'):
            file_source.seek(0)
        df = _read_student_workbook(file_source)

        columns = {
            'roll': detect_excel_column(df, ['RollNo', 'Roll No', 'Roll Number', 'Registration Number', 'Registration No', 'Reg No', 'Student ID', 'StudentId', 'Rollno']),
            'name': detect_excel_column(df, ['NameasPerXstd', 'StudentName', 'Student Name', 'Name', 'Full Name', 'NameAsPerXStd']),
            'email': detect_excel_column(df, ['EmailId', 'Email_Id', 'Email', 'Email ID', 'E-mail', 'Mail', 'Student Email']),
            'sess': detect_excel_column(df, ['studentSess', 'Student_Sess', 'Session', 'Student Session', 'Semester', 'Sess', 'StudentSess']),
            'course_code': detect_excel_column(df, ['CourseCode', 'Course Code', 'Course_Code', 'COURSE CODE', 'Course']),
            'credits': detect_excel_column(df, ['Credits', 'Credit', 'CREDITS']),
            'course_title': detect_excel_column(df, ['CourseTitle', 'Course Title', 'Course_Title', 'CourseName', 'Course Name', 'COURSE TITLE', 'Title']),
            'program': detect_excel_column(df, ['ProgramName', 'Program Name', 'Program', 'Programme', 'Degree', 'Branch']),
            'batch': detect_excel_column(df, ['SectionBatchName', 'Section Batch Name', 'Timetable_Batch', 'Batch', 'Time Table Batch', 'TimetableBatch', 'Section']),
            'slot': detect_excel_column(df, ['Slot_Code', 'Slot', 'Slot Code', 'SlotCode']),
            'instructor': detect_excel_column(df, ['Main_Instructor', 'Instructor', 'Main Instructor', 'Faculty']),
            'primary_mail': detect_excel_column(df, ['Primary_Mail', 'Primary Mail', 'PrimaryMail']),
            'category': detect_excel_column(df, ['Course_Category_Code', 'Category', 'Course Category', 'CategoryCode']),
            'section': detect_excel_column(df, ['Section', 'Student Section', 'Section Name']),
        }

        if not columns['roll']:
            return False, 'Error: Could not find Roll Number column in Excel file. Please ensure the file has a column for roll numbers.', None

        if sheet_type != 'combined':
            levels = df[columns['roll']].astype(str).map(get_program_level)
            df = df[levels == sheet_type].copy()

        students_data = _normalize_students(df, columns)

        db_name = get_semester_db_name(academic_year, semester_type, sheet_type, exam_type)
        create_semester_db(db_name)

        semester_id = upsert_semester_and_clear_students(
            academic_year,
            semester_type,
            sheet_type,
            exam_type,
            db_name,
        )

        for item in students_data:
            item['semester_id'] = semester_id

        inserted = replace_students_for_semester(semester_id, db_name, students_data)

        sheet_display = 'All Programs' if sheet_type == 'combined' else sheet_type
        return (
            True,
            f'Data loaded successfully for {academic_year} {semester_type} {sheet_display} {exam_type} ({inserted} records)',
            {'records': inserted, 'semester_id': semester_id},
        )
    except Exception as exc:
        return False, f'Error loading data: {str(exc)}', None
