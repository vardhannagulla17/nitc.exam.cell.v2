"""
Test semester display format
"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

with app.app_context():
    from app.models import get_all_semesters, get_semesters_for_program_level
    
    print("=== All Semesters (as shown on page) ===")
    semesters = get_all_semesters()
    for sem in semesters:
        # Format: "2025-26 Monsoon (COMBINED, Midsem)"
        display_name = f"{sem[1]} {sem[2].capitalize()} ({sem[3].upper()}, {sem[4].capitalize()})"
        print(f"ID {sem[0]}: {display_name}")
    
    print("\n=== Semesters for UG ===")
    ug_semesters = get_semesters_for_program_level('UG')
    for sem in ug_semesters:
        display_name = f"{sem[1]} {sem[2].capitalize()} ({sem[3].upper()}, {sem[4].capitalize()})"
        print(f"ID {sem[0]}: {display_name}")
