import pandas as pd
import re

from database.db_setup import create_semester_db, get_semester_db_name
from database.repository import replace_students_for_semester, upsert_semester_and_clear_students
from helpers.utils import get_program_level


def _normalize_token(value):
    return re.sub(r'[^a-z0-9]', '', str(value).strip().lower())


def _normalized_suffix(value):
    """Return the normalized trailing 'word' of a column header.

    Export tools (e.g. Syncfusion XlsIO) often prefix every column with a
    report/query name, such as 'MG_SaySupplementaryRegisteredStudents_Name'.
    Comparing whole-column substrings against short field names like 'Name'
    is ambiguous ('Name' is also a substring of '...CourseName'), so we also
    compare against just the last underscore/space/hyphen separated segment.
    """
    text = str(value).strip()
    parts = [part for part in re.split(r'[\s_\-:/]+', text) if part]
    return _normalize_token(parts[-1]) if parts else _normalize_token(text)


def detect_excel_column(df, possible_names):
    df_columns_norm = {_normalize_token(col): col for col in df.columns}
    df_columns_suffix = {}
    for col in df.columns:
        suffix = _normalized_suffix(col)
        df_columns_suffix.setdefault(suffix, col)

    candidates = [_normalize_token(name) for name in possible_names]

    # Pass 1: exact match against the full, normalized column name.
    for name_norm in candidates:
        if name_norm in df_columns_norm:
            return df_columns_norm[name_norm]

    # Pass 2: exact match against the final segment of the column name, so
    # prefixed headers resolve to the specific field they end with instead
    # of matching an unrelated column that merely contains the same text
    # (e.g. 'Name' should not match '..._CourseName').
    for name_norm in candidates:
        if name_norm in df_columns_suffix:
            return df_columns_suffix[name_norm]

    # Pass 3: loose substring fallback for anything unusual, used only as a
    # last resort once the stricter passes above have been exhausted.
    for name_norm in candidates:
        for col_norm, col_original in df_columns_norm.items():
            if name_norm in col_norm or col_norm in name_norm:
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


# Matches genuine NITC roll/registration numbers, e.g. B260117ME, M230045CS,
# P260102ME - one letter, six digits, then a two-to-four letter department
# code.
_ROLL_NO_PATTERN = re.compile(r'^[A-Z]\d{6}[A-Z]{2,4}$')


def _looks_like_roll_no(value):
    return bool(_ROLL_NO_PATTERN.match(_text_value(value).strip().upper()))


def _resolve_roll_and_name(row, columns):
    """Extract roll number and name for a row, correcting for ragged rows.

    Some source workbooks (e.g. Ph.D. registrations with no applicable
    semester number) omit an optional cell for a subset of rows. Excel/the
    export tool then compacts that row, shifting every later value one
    column to the left - so the 'RollNo' cell actually holds the student's
    name, and the 'Semester' cell actually holds the roll number, with the
    trailing 'Name' cell left blank. Detect that pattern per-row (rather
    than assuming it applies to the whole sheet) and recover the correct
    values instead of silently storing garbage.
    """
    roll_col = columns['roll']
    sess_col = columns['sess']
    name_col = columns['name']

    raw_roll = _text_value(row.get(roll_col, '')) if roll_col else ''
    raw_sess = _text_value(row.get(sess_col, '')) if sess_col else ''
    raw_name = _text_value(row.get(name_col, '')) if name_col else ''

    if roll_col and sess_col and not _looks_like_roll_no(raw_roll) and _looks_like_roll_no(raw_sess):
        # Row shifted left by one: recover the real roll number and name,
        # and treat the (missing) semester value as blank rather than wrong.
        return raw_sess.strip().upper(), raw_roll, ''

    return raw_roll.strip().upper(), raw_name, raw_sess


def _normalize_students(df, columns):
    students_data = []
    for _, row in df.iterrows():
        roll_no, name, student_sess = _resolve_roll_and_name(row, columns)
        if not roll_no and not name:
            # Skip fully blank rows (e.g. trailing empty rows in the sheet).
            continue
        students_data.append(
            {
                'roll_no': roll_no,
                'name': name,
                'email_id': _text_value(row.get(columns['email'], '')) if columns['email'] else '',
                'student_sess': student_sess,
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

        # Normalize first (this also repairs any ragged/shifted rows), then
        # filter by program level using the *corrected* roll number. Filtering
        # on the raw column before normalization would misclassify rows whose
        # roll number only becomes correct after the shift repair.
        students_data = _normalize_students(df, columns)

        if sheet_type != 'combined':
            students_data = [
                item for item in students_data
                if get_program_level(item['roll_no']) == sheet_type
            ]

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
