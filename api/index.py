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
        /* Professional Faculty Interface - Matching Login/Dashboard Design */
        :root {
            --bg-base: #f8fafc;
            --bg-elevated: #ffffff;
            --bg-surface: #f1f5f9;
            --bg-overlay: #e2e8f0;
            
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --primary-light: #3b82f6;
            --primary-soft: #dbeafe;
            
            --secondary: #6366f1;
            --success: #059669;
            --warning: #d97706;
            --info: #0891b2;
            
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #64748b;
            --text-muted: #94a3b8;
            
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            
            --radius-sm: 0.375rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
            --radius-2xl: 1.5rem;
            
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 0; min-height: 100vh;
            background: var(--bg-base);
            display: flex; align-items: center; justify-content: center;
            padding: 2rem;
        }
        
        .container {
            background: var(--bg-elevated);
            padding: 3rem;
            border-radius: var(--radius-2xl);
            text-align: center;
            max-width: 700px;
            width: 100%;
            border: 1px solid var(--border-light);
            position: relative;
            overflow: hidden;
            
            /* Professional layered shadows matching login page */
            box-shadow: 
                0 1px 3px rgba(0, 0, 0, 0.05),
                0 4px 16px rgba(0, 0, 0, 0.08),
                0 8px 32px rgba(0, 0, 0, 0.12);
                
            /* Subtle animation */
            animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .container:hover {
            box-shadow: 
                0 2px 6px rgba(0, 0, 0, 0.06),
                0 8px 24px rgba(0, 0, 0, 0.12),
                0 16px 48px rgba(0, 0, 0, 0.16);
        }
        
        /* Header gradient bar like dashboard */
        .container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 50%, var(--secondary) 100%);
        }
        
        .title {
            color: var(--text-primary);
            font-size: 2.75rem;
            margin-bottom: 1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.2;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 1.125rem;
            margin-bottom: 2.5rem;
            font-weight: 400;
            line-height: 1.6;
        }
        
        .buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 2.5rem;
        }
        
        .btn {
            padding: 0.875rem 1.75rem;
            border-radius: var(--radius-lg);
            text-decoration: none;
            font-weight: 600;
            color: white;
            font-size: 0.95rem;
            position: relative;
            overflow: hidden;
            border: none;
            cursor: pointer;
            
            /* Enhanced transitions */
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            transform: translateY(0);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .btn:active {
            transform: translateY(-1px);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            box-shadow: var(--shadow-md);
        }
        
        .btn-success {
            background: linear-gradient(135deg, var(--success) 0%, #10b981 100%);
            box-shadow: var(--shadow-md);
        }
        
        .btn-warning {
            background: linear-gradient(135deg, var(--warning) 0%, #f59e0b 100%);
            box-shadow: var(--shadow-md);
        }
        
        .status {
            margin-top: 2rem;
            padding: 1.5rem;
            background: var(--bg-surface);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            color: var(--text-tertiary);
            font-size: 0.875rem;
            line-height: 1.6;
            font-weight: 500;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(2rem);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Responsive adjustments */
        @media (max-width: 640px) {
            .container { padding: 2rem; margin: 1rem; }
            .title { font-size: 2.25rem; }
            .buttons { flex-direction: column; align-items: center; }
            .btn { width: 200px; }
        }
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
