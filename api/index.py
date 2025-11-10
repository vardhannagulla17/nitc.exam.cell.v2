# NITC Exam Cell - Vercel Deployment
# Ultra-robust Flask application for Vercel serverless

def create_application():
    """Create and configure Flask application"""
    
    print("🚀 Initializing NITC Exam Cell for Vercel...")
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
        
        app = Flask(__name__)
        app.secret_key = 'nitc-vercel-2024-secure'
        
        print("✅ Flask app created")
        
        # Root route
        @app.route('/')
        def home():
            try:
                print("📍 Home route accessed")
                return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NITC Exam Cell</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎓</text></svg>">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 0; min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex; align-items: center; justify-content: center;
        }
        .container {
            background: white; padding: 3rem; border-radius: 1rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            text-align: center; max-width: 600px; margin: 2rem;
        }
        .title { color: #1f2937; font-size: 2.5rem; margin-bottom: 1rem; font-weight: 700; }
        .subtitle { color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem; }
        .buttons { display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; }
        .btn {
            padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none;
            font-weight: 600; color: white; transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-primary { background: #3b82f6; }
        .btn-success { background: #10b981; }
        .btn-warning { background: #f59e0b; }
        .status { margin-top: 2rem; color: #9ca3af; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🎓 NITC Exam Cell</h1>
        <p class="subtitle">Successfully deployed on Vercel!</p>
        <div class="buttons">
            <a href="/test" class="btn btn-primary">API Test</a>
            <a href="/health" class="btn btn-success">Health Check</a>
            <a href="/demo" class="btn btn-warning">Demo Mode</a>
        </div>
        <div class="status">
            🚀 Vercel Serverless • ⚡ Python Flask • ✅ Operational
        </div>
    </div>
</body>
</html>"""
            except Exception as e:
                print(f"❌ Error in home route: {e}")
                return f'<h1>Home Route Error</h1><p>{str(e)}</p>', 500
        
        # API Test route
        @app.route('/test')
        def test():
            try:
                print("📍 Test route accessed")
                import sys, os
                return {
                    'status': 'success',
                    'app': 'NITC Exam Cell',
                    'platform': 'Vercel',
                    'python_version': sys.version.split()[0],
                    'working': True,
                    'routes': ['/', '/test', '/health', '/demo'],
                    'message': 'All systems operational! 🎉'
                }
            except Exception as e:
                print(f"❌ Error in test route: {e}")
                return {'error': str(e)}, 500
        
        # Health check route
        @app.route('/health')
        def health():
            try:
                print("📍 Health route accessed")
                return {
                    'status': 'healthy',
                    'timestamp': '2024-11-11',
                    'uptime': 'operational',
                    'services': {
                        'web': 'up',
                        'api': 'up'
                    }
                }
            except Exception as e:
                print(f"❌ Error in health route: {e}")
                return {'status': 'error', 'error': str(e)}, 500
        
        # Demo route
        @app.route('/demo')
        def demo():
            try:
                print("📍 Demo route accessed")
                return '<h1>🎓 NITC Exam Cell Demo</h1><p>Coming Soon: Full application features</p><a href="/">← Back Home</a>'
            except Exception as e:
                print(f"❌ Error in demo route: {e}")
                return f'<h1>Demo Error</h1><p>{str(e)}</p>', 500
        
        # Favicon routes
        @app.route('/favicon.ico')
        @app.route('/favicon.png')
        def favicon():
            print("📍 Favicon requested")
            # Return empty response with no content
            from flask import Response
            return Response('', mimetype='image/x-icon')
        
        # 404 handler
        @app.errorhandler(404)
        def not_found(error):
            print(f"📍 404 error: {error}")
            return '<h1>Page Not Found</h1><p>The requested page could not be found.</p><a href="/">← Go Home</a>', 404
        
        # General error handler
        @app.errorhandler(Exception)
        def handle_exception(error):
            print(f"📍 Exception caught: {error}")
            import traceback
            traceback.print_exc()
            return f'<h1>Application Error</h1><p>Error: {str(error)}</p><a href="/">← Go Home</a>', 500
        
        print("✅ All routes configured")
        print("✅ NITC Exam Cell ready for Vercel!")
        
        return app
        
    except ImportError as ie:
        print(f"❌ IMPORT ERROR: {ie}")
        raise ie
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise e

# Initialize the application
try:
    app = create_application()
    print("🎉 Application successfully created!")
except Exception as e:
    print(f"💥 FATAL: Could not create application: {e}")
    # Emergency fallback
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def emergency():
        return f'<h1>Emergency Mode</h1><p>Initialization failed: {str(e)}</p>'
    
    @app.route('/favicon.ico')
    def emergency_favicon():
        return '', 204
