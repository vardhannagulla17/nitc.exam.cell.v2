try:
    print("Starting Vercel app initialization...")
    
    from flask import Flask
    print("Flask imported successfully")
    
    # Create minimal Flask app
    app = Flask(__name__)
    print("Flask app created")
    
    app.secret_key = 'vercel-test-key'
    
    @app.route('/')
    def index():
        return '''
        <html>
        <head><title>NITC Exam Cell - Vercel Test</title></head>
        <body style="font-family: Arial; padding: 40px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; margin: 0;">
            <div style="background: white; padding: 40px; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto;">
                <h1 style="color: #1f2937; margin-bottom: 20px;">🎓 NITC Exam Cell</h1>
                <p style="color: #6b7280; margin-bottom: 30px;">Vercel deployment successful! The application is running.</p>
                <div style="margin: 20px 0;">
                    <a href="/test" style="background: #667eea; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin: 0 10px; display: inline-block;">Test Page</a>
                    <a href="/health" style="background: #10b981; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin: 0 10px; display: inline-block;">Health Check</a>
                </div>
                <p style="color: #9ca3af; font-size: 14px; margin-top: 30px;">
                    🚀 Deployed on Vercel • ⚡ Serverless Python
                </p>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/test')
    def test():
        return {
            'status': 'success',
            'message': 'NITC Exam Cell API is working',
            'vercel': True,
            'routes': [
                '/ - Home page',
                '/test - This test endpoint',
                '/health - Health check',
                '/simple - Simple text response'
            ]
        }
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'app': 'NITC Exam Cell', 'platform': 'Vercel'}
    
    @app.route('/simple')
    def simple():
        return 'NITC Exam Cell - Simple response working!'
    
    @app.errorhandler(Exception)
    def handle_error(e):
        print(f"Error occurred: {e}")
        return f'<h1>Error</h1><p>Something went wrong: {str(e)}</p><a href="/">Go back home</a>', 500
    
    print("All routes defined successfully")
    print("App initialization complete!")

except ImportError as e:
    print(f"Import error: {e}")
    # Create absolute minimal app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        return f'<h1>Import Error</h1><p>{str(e)}</p>'

except Exception as e:
    print(f"Critical error: {e}")
    import traceback
    traceback.print_exc()
    
    # Last resort minimal app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def critical_error():
        return f'<h1>Critical Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>'
