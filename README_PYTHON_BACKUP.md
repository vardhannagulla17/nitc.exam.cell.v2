# BACKUP - Original Python/Flask Version

**⚠️ This branch contains the ORIGINAL Python/Flask implementation**

## About This Branch

This is the backup of the working Python/Flask version before migration to Node.js.

- **Technology**: Python 3.x + Flask + SQLite/PostgreSQL (Supabase)
- **Status**: ✅ Fully functional production code
- **Date Backed Up**: March 18, 2026
- **Purpose**: Backup and reference for Python implementation

## What's on This Branch

- Original Flask application (`app.py`, `api/index.py`)
- Python models and routes (`app/models.py`, `app/routes.py`)
- Jinja2 templates (`templates/*.html`)
- Python dependencies (`requirements.txt`)
- All Python helper utilities

## To Run This Version

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Or deploy to Vercel (configured for Python)
vercel --prod
```

## Migration Information

The Node.js version is on the `main` branch.

- See `SETUP_NODE.md` for Node.js setup
- See `MIGRATION_SUMMARY_NODE.md` for migration details
- Both versions have feature parity

## Don't Delete This Branch!

This is your working backup. Keep it for:
- Reference when debugging
- Reverting if needed
- Comparing implementations
- Learning differences between Flask and Express

---

**Main branch**: Node.js/Express version
**This branch**: Python/Flask backup (original working version)
