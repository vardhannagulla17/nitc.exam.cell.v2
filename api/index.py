from flask import Flask, request, redirect, session

def create_application():
    app = Flask(__name__)
    app.secret_key = 'nitc-vercel-secret'
    
    @app.route('/')
    def home():
        return redirect('/login')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            if username:
                session['user'] = username
                return redirect('/dashboard')
        
        return '''<!DOCTYPE html>
<html><head><title>NITC Login</title>
<style>
body{font-family:Arial;background:#f8fafc;margin:0;padding:2rem;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{background:white;padding:3rem;border-radius:1rem;box-shadow:0 10px 25px rgba(0,0,0,0.1);max-width:400px;width:100%}
h1{color:#2563eb;text-align:center;margin-bottom:2rem}
.form-group{margin-bottom:1.5rem}
label{display:block;margin-bottom:0.5rem;font-weight:600}
input{width:100%;padding:0.75rem;border:1px solid #e2e8f0;border-radius:0.5rem;font-size:1rem}
button{width:100%;background:#2563eb;color:white;padding:0.75rem;border:none;border-radius:0.5rem;font-size:1rem;font-weight:600;cursor:pointer}
button:hover{background:#1d4ed8}
</style></head>
<body>
<div class=container>
<h1> NITC Exam Cell</h1>
<form method=post>
<div class=form-group><label>Username</label><input name=username required></div>
<div class=form-group><label>Password</label><input type=password name=password required></div>
<button type=submit>Login</button>
</form>
</div>
</body></html>'''
    
    @app.route('/dashboard')
    def dashboard():
        if 'user' not in session:
            return redirect('/login')
        
        return '''<!DOCTYPE html>
<html><head><title>NITC Dashboard</title>
<style>
body{font-family:Arial;background:#f8fafc;margin:0;padding:2rem}
.container{max-width:1200px;margin:0 auto}
.header{background:white;padding:2rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin-bottom:2rem;text-align:center}
.header h1{color:#2563eb;margin-bottom:0.5rem}
.nav-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1.5rem;margin-bottom:2rem}
.nav-card{background:white;padding:2rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);text-decoration:none;color:#0f172a;text-align:center;transition:transform 0.3s}
.nav-card:hover{transform:translateY(-4px)}
.nav-card h3{color:#2563eb;margin-bottom:0.5rem}
.logout{text-align:center}
.logout-btn{background:#dc2626;color:white;padding:0.75rem 2rem;border-radius:0.5rem;text-decoration:none;font-weight:600}
</style></head>
<body>
<div class=container>
<div class=header>
<h1> Dashboard</h1>
<p>Welcome to NITC Exam Cell</p>
</div>
<div class=nav-grid>
<a href=/upload class=nav-card><h3> Upload</h3><p>Upload files</p></a>
<a href=/download class=nav-card><h3> Download</h3><p>Download reports</p></a>
<a href=/api/students class=nav-card><h3> API</h3><p>Student data API</p></a>
</div>
<div class=logout><a href=/logout class=logout-btn>Logout</a></div>
</div>
</body></html>'''
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if 'user' not in session:
            return redirect('/login')
        
        if request.method == 'POST':
            return redirect('/upload?msg=uploaded')
        
        return '''<!DOCTYPE html>
<html><head><title>NITC Upload</title>
<style>
body{font-family:Arial;background:#f8fafc;margin:0;padding:2rem}
.container{max-width:800px;margin:0 auto}
.back-btn{background:#2563eb;color:white;padding:0.5rem 1rem;border-radius:0.5rem;text-decoration:none;margin-bottom:2rem;display:inline-block}
.header{background:white;padding:2rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin-bottom:2rem;text-align:center}
.upload-area{background:white;padding:3rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);text-align:center}
input[type=file]{width:100%;padding:1rem;border:2px dashed #2563eb;border-radius:0.5rem;margin:2rem 0}
button{background:#2563eb;color:white;padding:0.75rem 2rem;border:none;border-radius:0.5rem;font-weight:600;cursor:pointer}
</style></head>
<body>
<div class=container>
<a href=/dashboard class=back-btn> Back</a>
<div class=header><h1> Upload Files</h1></div>
<div class=upload-area>
<form method=post enctype=multipart/form-data>
<div></div>
<p>Select Excel file to upload</p>
<input type=file name=file accept=.xlsx,.xls,.csv required>
<button type=submit>Upload File</button>
</form>
</div>
</div>
</body></html>'''
    
    @app.route('/download')
    def download():
        if 'user' not in session:
            return redirect('/login')
        return '''<!DOCTYPE html>
<html><head><title>NITC Download</title>
<style>
body{font-family:Arial;background:#f8fafc;margin:0;padding:2rem}
.container{max-width:800px;margin:0 auto}
.back-btn{background:#2563eb;color:white;padding:0.5rem 1rem;border-radius:0.5rem;text-decoration:none;margin-bottom:2rem;display:inline-block}
.header{background:white;padding:2rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin-bottom:2rem;text-align:center}
.download-area{background:white;padding:3rem;border-radius:1rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);text-align:center}
</style></head>
<body>
<div class=container>
<a href=/dashboard class=back-btn> Back</a>
<div class=header><h1> Download Files</h1></div>
<div class=download-area>
<div></div>
<p>Download functionality coming soon!</p>
</div>
</div>
</body></html>'''
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect('/login')
    
    @app.route('/api/students')
    def api_students():
        return {'status': 'success', 'students': []}
    
    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    return app

app = create_application()
