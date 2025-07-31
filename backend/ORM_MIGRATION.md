# Database ORM Migration Guide

This document describes the migration from raw SQL queries to SQLAlchemy ORM in the Serbian Vocabulary App backend.

## What Changed

### 1. **New Dependencies**

- Added `flask-sqlalchemy==3.1.1` and `sqlalchemy==2.0.23` to `requirements.txt`

### 2. **New Files**

- `models.py` - Contains all SQLAlchemy model definitions
- `migrate.py` - Database migration utility script
- `app_raw_sql.py` - Backup of the original app.py using raw SQL

### 3. **Model Structure**

The following models were created to match the existing database schema:

#### Category Model

```python
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Word Model

```python
class Word(db.Model):
    __tablename__ = 'words'
    id = db.Column(db.Integer, primary_key=True)
    serbian_word = db.Column(db.String(255), nullable=False)
    english_translation = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    # ... additional fields
```

#### UserVocabulary Model

```python
class UserVocabulary(db.Model):
    __tablename__ = 'user_vocabulary'
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    times_practiced = db.Column(db.Integer, default=0)
    # ... additional fields
```

#### PracticeSession Model

```python
class PracticeSession(db.Model):
    __tablename__ = 'practice_sessions'
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.DateTime, default=datetime.utcnow)
    # ... additional fields
```

#### PracticeResult Model

```python
class PracticeResult(db.Model):
    __tablename__ = 'practice_results'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('practice_sessions.id'))
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'))
    # ... additional fields
```

## Benefits of Using ORM

1. **Type Safety**: Models provide clear structure and type hints
2. **Relationships**: Easy navigation between related data using SQLAlchemy relationships
3. **Query Building**: More readable and maintainable queries
4. **Automatic Escaping**: Protection against SQL injection
5. **Database Agnostic**: Easier to switch between different databases
6. **Migration Support**: Better schema version control
7. **Less Boilerplate**: No need for manual cursor management

## Examples of Changes

### Before (Raw SQL)

```python
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT * FROM categories ORDER BY name")
categories = cur.fetchall()
cur.close()
```

### After (ORM)

```python
categories = Category.query.order_by(Category.name).all()
```

### Before (Raw SQL with JOIN)

```python
query = """
    SELECT w.*, c.name as category_name, uv.mastery_level, uv.times_practiced
    FROM words w
    LEFT JOIN categories c ON w.category_id = c.id
    LEFT JOIN user_vocabulary uv ON w.id = uv.word_id
"""
cur.execute(query)
```

### After (ORM with eager loading)

```python
words = Word.query.options(
    joinedload(Word.category),
    joinedload(Word.user_vocabulary)
).all()
```

## Database Migration Utility

The `migrate.py` script provides several useful functions:

1. **Create Tables**: Create all tables from models
2. **Drop Tables**: Remove all tables (with confirmation)
3. **Seed Categories**: Add default categories
4. **Show Statistics**: Display record counts for all tables
5. **Check Connection**: Verify database connectivity

### Usage

```bash
python migrate.py
```

## Running the Application

The application works exactly the same as before. No changes are needed to:

- Docker configuration
- Frontend code
- API endpoints
- Environment variables

Simply rebuild and run:

```bash
docker-compose down
docker-compose up --build
```

## Rollback Instructions

If you need to rollback to the raw SQL version:

1. Rename files:

   ```bash
   mv app.py app_orm.py
   mv app_raw_sql.py app.py
   ```

2. Remove SQLAlchemy from requirements.txt:

   ```bash
   # Remove these lines:
   # flask-sqlalchemy==3.1.1
   # sqlalchemy==2.0.23
   ```

3. Rebuild the Docker container

## Performance Considerations

- The ORM adds minimal overhead for most operations
- Complex queries can be optimized using SQLAlchemy's query options
- For bulk operations, SQLAlchemy provides bulk insert/update methods
- Connection pooling is configured for optimal performance

## Future Enhancements

With ORM in place, you can now easily:

- Add database migrations using Flask-Migrate
- Implement more complex relationships
- Add model validation
- Create database indexes through model definitions
- Implement soft deletes
- Add audit trails
