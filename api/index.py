# NITC Exam Cell - Vercel Deployment
def create_application():
    print('Initializing NITC Exam Cell for Vercel...')
    
    try:
        import sys, os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, project_root)
        
        try:
            from app import app
            print('Main Flask app imported successfully')
            if not app.secret_key:
                app.secret_key = 'nitc-vercel-2024'
            return app
            
        except ImportError as e:
            print('Creating fallback app with routes...')
            from flask import Flask, render_template, request, redirect, session, flash
            
            app = Flask(__name__, 
                       template_folder=os.path.join(project_root, 'templates'),
                       static_folder=os.path.join(project_root, 'static'))
            app.secret_key = 'nitc-vercel-2024'
            
            @app.route('/')
            def home():
                return redirect('/login')
            
            @app.route('/login', methods=['GET', 'POST'])
            def login():
                if request.method == 'POST':
                    username = request.form.get('username')
                    password = request.form.get('password')
                    if username and password:
                        session['user'] = username
                        return redirect('/dashboard')
                try:
                    return render_template('login.html')
                except:
                    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - NITC Exam Cell</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎓</text></svg>">
    <style>
        :root {
            --bg-base: #f8fafc;
            --bg-elevated: #ffffff;
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --radius-lg: 0.75rem;
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .login-container {
            background: var(--bg-elevated);
            padding: 3rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            width: 100%;
            max-width: 400px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .login-container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        }
        
        .login-title {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .login-subtitle {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
            text-align: left;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .form-input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .login-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 0.75rem;
            border: none;
            border-radius: var(--radius-lg);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-lg);
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(37, 99, 235, 0.4);
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1 class="login-title">🎓 NITC Exam Cell</h1>
        <p class="login-subtitle">Faculty Login Portal</p>
        
        <form method="post">
            <div class="form-group">
                <label class="form-label" for="username">Username</label>
                <input class="form-input" type="text" id="username" name="username" placeholder="Enter your username" required>
            </div>
            
            <div class="form-group">
                <label class="form-label" for="password">Password</label>
                <input class="form-input" type="password" id="password" name="password" placeholder="Enter your password" required>
            </div>
            
            <button type="submit" class="login-btn">Login to Dashboard</button>
        </form>
    </div>
</body>
</html>'''
            
            @app.route('/dashboard')
            def dashboard():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('dashboard.html')
                except:
                    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - NITC Exam Cell</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎓</text></svg>">
    <style>
        :root {
            --bg-base: #f8fafc;
            --bg-elevated: #ffffff;
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --radius-lg: 0.75rem;
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            background: var(--bg-elevated);
            padding: 2rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .nav-card {
            background: var(--bg-elevated);
            padding: 2rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            text-decoration: none;
            color: var(--text-primary);
            transition: all 0.3s ease;
            border: 1px solid var(--border);
            text-align: center;
        }
        
        .nav-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        .nav-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }
        
        .nav-card p {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .logout-section {
            text-align: center;
            padding: 2rem;
        }
        
        .logout-btn {
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            color: white;
            padding: 0.75rem 2rem;
            border: none;
            border-radius: var(--radius-lg);
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-lg);
        }
        
        .logout-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 25px -5px rgba(220, 38, 38, 0.4);
        }
        
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .header h1 { font-size: 2rem; }
            .nav-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Dashboard</h1>
            <p>Welcome to NITC Exam Cell Management System</p>
        </div>
        
        <div class="nav-grid">
            <a href="/upload" class="nav-card">
                <h3>📤 Upload</h3>
                <p>Upload student data and exam files</p>
            </a>
            
            <a href="/download" class="nav-card">
                <h3>📥 Download</h3>
                <p>Download reports and exam data</p>
            </a>
            
            <a href="/api/students" class="nav-card">
                <h3>🔌 API</h3>
                <p>Access student data via API</p>
            </a>
        </div>
        
        <div class="logout-section">
            <a href="/logout" class="logout-btn">🚪 Logout</a>
        </div>
    </div>
</body>
</html>'''
            
            @app.route('/upload')
            def upload():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('upload.html')
                except:
                    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload - NITC Exam Cell</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎓</text></svg>">
    <style>
        :root {
            --bg-base: #f8fafc;
            --bg-elevated: #ffffff;
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --radius-lg: 0.75rem;
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            background: var(--bg-elevated);
            padding: 2rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        }
        
        .back-btn {
            background: var(--primary);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: var(--radius-lg);
            text-decoration: none;
            display: inline-block;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .back-btn:hover {
            background: var(--primary-light);
            transform: translateY(-2px);
        }
        
        .upload-area {
            background: var(--bg-elevated);
            padding: 3rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            text-align: center;
            border: 2px dashed var(--border);
        }
        
        .upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .upload-text {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        
        .upload-note {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/dashboard" class="back-btn">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📤 Upload Files</h1>
            <p>Upload student data and exam files</p>
        </div>
        
        <div class="upload-area">
            <div class="upload-icon">📁</div>
            <div class="upload-text">Upload functionality coming soon!</div>
            <div class="upload-note">This feature will be available in the full deployment</div>
        </div>
    </div>
</body>
</html>'''
            
            @app.route('/download')
            def download():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('download.html')
                except:
                    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-1.0">
    <title>Download - NITC Exam Cell</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎓</text></svg>">
    <style>
        :root {
            --bg-base: #f8fafc;
            --bg-elevated: #ffffff;
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --radius-lg: 0.75rem;
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            background: var(--bg-elevated);
            padding: 2rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        }
        
        .back-btn {
            background: var(--primary);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: var(--radius-lg);
            text-decoration: none;
            display: inline-block;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .back-btn:hover {
            background: var(--primary-light);
            transform: translateY(-2px);
        }
        
        .download-area {
            background: var(--bg-elevated);
            padding: 3rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            text-align: center;
        }
        
        .download-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .download-text {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        
        .download-note {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/dashboard" class="back-btn">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📥 Download Files</h1>
            <p>Download reports and exam data</p>
        </div>
        
        <div class="download-area">
            <div class="download-icon">📊</div>
            <div class="download-text">Download functionality coming soon!</div>
            <div class="download-note">This feature will be available in the full deployment</div>
        </div>
    </div>
</body>
</html>'''
            
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
            
    except Exception as e:
        from flask import Flask
        app = Flask(__name__)
        @app.route('/')
        def emergency():
            return f'Error: {str(e)}'
        return app

app = create_application()
