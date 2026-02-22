"""Test PDF generation locally"""
from io import BytesIO
from xhtml2pdf import pisa

# Simple test HTML matching our format
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test PDF</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 10px; 
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 8px 0; 
        }
        th, td { 
            border: 1px solid black; 
            padding: 4px; 
            text-align: left; 
            font-size: 10px; 
        }
        th { 
            background-color: #f0f0f0; 
            font-weight: bold; 
        }
    </style>
</head>
<body>
    <div class="header">
        <div style="font-weight: bold; font-size: 14px;">NATIONAL INSTITUTE OF TECHNOLOGY CALICUT</div>
        <div style="font-weight: bold; font-size: 12px; margin-top: 3px;">DEPARTMENT OF MECHANICAL ENGINEERING</div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 5%;">Sl. No.</th>
                <th style="width: 12%;">Roll No.</th>
                <th style="width: 7%;">Batch</th>
                <th style="width: 32%;">Student Name</th>
                <th style="width: 13%;">No. of Additional Sheets</th>
                <th style="width: 16%;">Details of Bio Break</th>
                <th style="width: 15%;">Signature</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>B230396ME</td>
                <td>ME02</td>
                <td>LAUDYAVATH BHANUCHANDER</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>2</td>
                <td>B230397ME</td>
                <td>ME02</td>
                <td>LEO JOSEPH</td>
                <td></td>
                <td></td>
                <td></td>
            </tr>
        </tbody>
    </table>

    <table>
        <tr>
            <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of the answer Books</th>
            <th colspan="3" style="background-color: #d3d3d3; text-align: center;">Details of the Invigilators</th>
        </tr>
        <tr>
            <td style="width: 12%;"></td>
            <th style="width: 8%; text-align: center;">Main</th>
            <th style="width: 13%; text-align: center;">Additional</th>
            <th style="width: 10%; text-align: center;">Sl. No.</th>
            <th style="width: 35%; text-align: center;">Name</th>
            <th style="width: 22%; text-align: center;">Signature</th>
        </tr>
        <tr>
            <td><strong>Received</strong></td>
            <td></td>
            <td></td>
            <td style="text-align: center;">1</td>
            <td></td>
            <td></td>
        </tr>
    </table>
</body>
</html>"""

print("Generating test PDF...")
result = BytesIO()
pdf = pisa.pisaDocument(BytesIO(html_content.encode("utf-8")), result)

if pdf.err:
    print(f"✗ PDF generation had errors: {pdf.err}")
else:
    print(f"✓ PDF generated successfully")
    
    # Save to file
    with open('test_output.pdf', 'wb') as f:
        f.write(result.getvalue())
    print(f"  Saved to test_output.pdf ({len(result.getvalue())} bytes)")
    print("\nPlease open test_output.pdf to see if tables render correctly!")
