from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    return db
