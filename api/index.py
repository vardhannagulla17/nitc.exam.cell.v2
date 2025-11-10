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
                    return '<h1>Login</h1><form method=post><input name=username placeholder=Username><input name=password type=password placeholder=Password><button>Login</button></form>'
            
            @app.route('/dashboard')
            def dashboard():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('dashboard.html')
                except:
                    return '<h1>Dashboard</h1><a href=/upload>Upload</a> | <a href=/download>Download</a> | <a href=/logout>Logout</a>'
            
            @app.route('/upload')
            def upload():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('upload.html')
                except:
                    return '<h1>Upload</h1><a href=/dashboard>Back</a>'
            
            @app.route('/download')
            def download():
                if 'user' not in session:
                    return redirect('/login')
                try:
                    return render_template('download.html')
                except:
                    return '<h1>Download</h1><a href=/dashboard>Back</a>'
            
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
