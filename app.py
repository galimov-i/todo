"""Main Flask application for Kanban Board with Time Tracking."""
from flask import Flask, render_template, jsonify
from config import Config, TaskStatus
from database import init_app, init_db
from routes import tasks_bp, timer_bp


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    init_app(app)
    
    # Register blueprints
    app.register_blueprint(tasks_bp)
    app.register_blueprint(timer_bp)
    
    # Main page route
    @app.route('/')
    def index():
        """Render the main Kanban board page."""
        return render_template('index.html', columns=TaskStatus.DISPLAY_NAMES)
    
    # Health check endpoint
    @app.route('/api/health')
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'ok'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    import os
    from config import DATABASE_PATH
    
    if not os.path.exists(DATABASE_PATH):
        with app.app_context():
            init_db()
            print("Database initialized!")
    
    # Run the development server
    app.run(host='0.0.0.0', port=5000, debug=True)
