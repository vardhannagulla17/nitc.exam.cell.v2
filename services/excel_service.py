import pandas as pd

from database.db_setup import create_semester_db, get_semester_db_name
from database.repository import replace_students_for_semester, upsert_semester_and_clear_students
from helpers.utils import get_program_level


def detect_excel_column(df, possible_names):
    df_columns_lower = {col.lower(): col for col in df.columns}
    for name in possible_names:
        name_lower = name.lower()
        if name_lower in df_columns_lower:
            return df_columns_lower[name_lower]
        for col_lower, col_original in df_columns_lower.items():
            if name_lower in col_lower or col_lower in name_lower:
                return col_original
    return None


def _normalize_students(df, columns):
    students_data = []
    for _, row in df.iterrows():
        students_data.append(
            {
                'roll_no': str(row.get(columns['roll'], '')) if columns['roll'] else '',
                'name': str(row.get(columns['name'], '')) if columns['name'] else '',
                'email_id': str(row.get(columns['email'], '')) if columns['email'] else '',
                'student_sess': str(row.get(columns['sess'], '')) if columns['sess'] else '',
                'course_code': str(row.get(columns['course_code'], '')) if columns['course_code'] else '',
                'credits': int(row.get(columns['credits'], 0)) if columns['credits'] and pd.notna(row.get(columns['credits'])) else 0,
                'course_title': str(row.get(columns['course_title'], '')) if columns['course_title'] else '',
                'program_name': str(row.get(columns['program'], '')) if columns['program'] else '',
                'timetable_batch': str(row.get(columns['batch'], '')) if columns['batch'] else '',
                'slot_code': str(row.get(columns['slot'], '')) if columns['slot'] else '',
                'main_instructor': str(row.get(columns['instructor'], '')).strip() if columns['instructor'] else '',
                'primary_mail': str(row.get(columns['primary_mail'], '')) if columns['primary_mail'] else '',
                'course_category_code': str(row.get(columns['category'], '')) if columns['category'] else '',
            }
        )
    return students_data


def load_excel_to_db(file_source, academic_year, semester_type, sheet_type, exam_type):
    try:
        df = pd.read_excel(file_source, engine='openpyxl')

        columns = {
            'roll': detect_excel_column(df, ['RollNo', 'Roll No', 'Roll_No', 'ROLL NO', 'Roll Number', 'Rollno']),
            'name': detect_excel_column(df, ['NameasPerXstd', 'StudentName', 'Student Name', 'Name', 'STUDENT NAME', 'Student_Name', 'STUDENTNAME', 'NameAsPerXStd']),
            'email': detect_excel_column(df, ['EmailId', 'Email_Id', 'Email', 'Email ID', 'E-mail', 'Mail']),
            'sess': detect_excel_column(df, ['studentSess', 'Student_Sess', 'Session', 'Student Session', 'Sess', 'StudentSess']),
            'course_code': detect_excel_column(df, ['CourseCode', 'Course Code', 'Course_Code', 'COURSE CODE']),
            'credits': detect_excel_column(df, ['Credits', 'Credit', 'CREDITS']),
            'course_title': detect_excel_column(df, ['CourseTitle', 'Course Title', 'Course_Title', 'COURSE TITLE', 'Title']),
            'program': detect_excel_column(df, ['ProgramName', 'Program Name', 'Program', 'PROGRAM NAME', 'Programme']),
            'batch': detect_excel_column(df, ['SectionBatchName', 'Section Batch Name', 'Timetable_Batch', 'Batch', 'Time Table Batch', 'TimetableBatch']),
            'slot': detect_excel_column(df, ['Slot_Code', 'Slot', 'Slot Code', 'SlotCode']),
            'instructor': detect_excel_column(df, ['Main_Instructor', 'Instructor', 'Main Instructor', 'Faculty']),
            'primary_mail': detect_excel_column(df, ['Primary_Mail', 'Primary Mail', 'PrimaryMail']),
            'category': detect_excel_column(df, ['Course_Category_Code', 'Category', 'Course Category', 'CategoryCode']),
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
