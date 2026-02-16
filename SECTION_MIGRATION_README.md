# Section Filtering Migration - IMPORTANT

## ⚠️ ACTION REQUIRED: Run Database Migration

To enable section filtering in the absentee marking system, you need to add the `section` column to the `students` table in your Supabase database.

## Step-by-Step Instructions:

### 1. Open Supabase SQL Editor
   - Go to your Supabase project: https://supabase.com/dashboard
   - Navigate to "SQL Editor" in the left sidebar
   - Click "New Query"

### 2. Run the Migration SQL
   Copy and paste the following SQL command:

```sql
-- Add section column to students table
ALTER TABLE students ADD COLUMN IF NOT EXISTS section TEXT;

-- Create index for section filtering
CREATE INDEX IF NOT EXISTS idx_students_section ON students(section);

-- Add comment
COMMENT ON COLUMN students.section IS 'Student section/batch identifier (e.g., ME01, EC02, etc.)';
```

### 3. Click "Run" to execute the migration

### 4. Verify the Migration
   Run this query to confirm the column was added:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'students' AND column_name = 'section';
```

You should see the `section` column listed.

## What This Enables:

✅ **Optional Section Filtering**: When loading students for a course, you can now:
- Leave section blank → Get ALL students in that course
- Enter a section (e.g., ME01, EC02) → Get only students from that section

✅ **Better Organization**: Students can be grouped by sections for easier absent marking

✅ **Flexible Workflow**: Section field remains optional - works with or without section data

## Updating Existing Data (Optional)

If you want to populate the section field for existing students, you can update it based on your data structure. For example:

```sql
-- If section info is in timetable_batch column
UPDATE students 
SET section = substring(timetable_batch from 1 for 4) 
WHERE section IS NULL AND timetable_batch IS NOT NULL;

-- Or manually set for specific courses
UPDATE students 
SET section = 'ME01' 
WHERE course_code = 'ME6323E' AND roll_no LIKE 'B2%ME';
```

## Troubleshooting

If you get an error like "column students.section does not exist":
- Make sure you've run the migration SQL in Supabase
- Refresh your application after running the migration
- Check that you're connected to the correct Supabase project

---

**Note**: The migration is idempotent (safe to run multiple times) thanks to the `IF NOT EXISTS` clause.
