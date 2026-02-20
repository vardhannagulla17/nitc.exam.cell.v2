# Vercel PDF Generation Fix

## Problem
When deploying to Vercel, you may encounter this error during build:
```
Did not find CMake 'cmake'
Found CMake: NO
Run-time dependency cairo found: NO (tried pkgconfig)
ERROR: Dependency "cairo" not found, tried pkgconfig
```

This happens because `pycairo` (a transitive dependency) requires system libraries (Cairo, CMake) that aren't available in Vercel's serverless environment.

## Solution

### Option 1: Pin Dependencies (Recommended - Already Applied)
We've pinned specific versions of dependencies that don't require system libraries:
- `reportlab==3.6.13` (older version without Cairo requirement)
- `xhtml2pdf==0.2.13`
- `html5lib==1.1`
- `pypdf==3.17.4`

### Option 2: Alternative PDF Library
If issues persist, consider using `weasyprint` with a custom build or `reportlab` directly:

```python
# Instead of xhtml2pdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Generate PDF directly
def generate_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    # ... add content
    p.save()
    return buffer
```

### Option 3: Use Vercel Build Settings
Add to `vercel.json`:
```json
{
  "build": {
    "env": {
      "PYTHON_VERSION": "3.9"
    }
  },
  "functions": {
    "api/index.py": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

## Testing
After updating requirements.txt, test locally:
```bash
pip install -r requirements.txt
python app.py
```

## Current Status
✅ Requirements.txt has been updated with pinned versions
✅ The application should now deploy successfully on Vercel
