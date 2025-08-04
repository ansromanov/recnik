# Issue 3: Database Schema and Performance Issues

## Problem Description

The database schema has several critical issues including missing foreign keys, inefficient indexes, and performance bottlenecks that cause slow queries and data integrity problems.

## Impact

- **Slow Queries**: Database queries take too long to execute
- **Data Integrity Issues**: Missing foreign key constraints allow orphaned data
- **Scalability Problems**: Database doesn't scale with user growth
- **Maintenance Issues**: Difficult to maintain data consistency

## Root Causes

### 1. Missing Foreign Key Constraints

```sql
-- In init.sql - practice_sessions missing user_id
CREATE TABLE practice_sessions (
    id SERIAL PRIMARY KEY,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- MISSING: user_id INTEGER REFERENCES users(id)
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    duration_seconds INTEGER
);
```

### 2. Inefficient Indexes

```sql
-- Missing critical indexes for performance
-- No index on user_vocabulary(user_id)
-- No index on practice_sessions(user_id)
-- No composite indexes for common queries
```

### 3. N+1 Query Problems

```python
# In app.py - causes multiple database hits
words = Word.query.filter_by(category_id=category_id).all()
for word in words:
    # Additional query for each word
    user_vocab = UserVocabulary.query.filter_by(
        user_id=user_id,
        word_id=word.id
    ).first()
```

### 4. Missing Database Constraints

```sql
-- No unique constraints on important combinations
-- No check constraints for data validation
-- No proper cascade delete rules
```

## Evidence from Codebase

### Schema Inconsistencies

```sql
-- init.sql vs models.py mismatch
-- init.sql doesn't have user_id in practice_sessions
-- models.py expects user_id foreign key
```

### Performance Issues

```python
# In app.py - inefficient queries
@app.route("/api/words")
@jwt_required()
def get_words():
    # No eager loading
    # No pagination
    # No filtering optimization
    words = Word.query.all()  # Loads ALL words
```

### Missing Indexes

```sql
-- performance_indexes.sql shows missing indexes
-- But they're not applied to the database
-- Critical indexes for user_vocabulary missing
```

## Solutions

### 1. Fix Database Schema

```sql
-- Add missing foreign key to practice_sessions
ALTER TABLE practice_sessions
ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_date
ON practice_sessions(user_id, session_date);

CREATE INDEX IF NOT EXISTS idx_user_vocabulary_user_mastery
ON user_vocabulary(user_id, mastery_level);
```

### 2. Implement Proper Constraints

```sql
-- Add unique constraints
ALTER TABLE user_vocabulary
ADD CONSTRAINT unique_user_word
UNIQUE(user_id, word_id);

-- Add check constraints
ALTER TABLE words
ADD CONSTRAINT check_difficulty
CHECK (difficulty_level >= 1 AND difficulty_level <= 5);
```

### 3. Optimize Queries

```python
# Use eager loading to prevent N+1 queries
words = Word.query.options(
    joinedload(Word.user_vocabulary),
    joinedload(Word.category)
).filter_by(category_id=category_id).all()

# Add pagination
@app.route("/api/words")
@jwt_required()
def get_words():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    words = Word.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    return jsonify({
        'words': [word.to_dict() for word in words.items],
        'total': words.total,
        'pages': words.pages,
        'current_page': page
    })
```

### 4. Add Database Migrations

```python
# Create proper migration system
# migrations/add_user_id_to_practice_sessions.py
def upgrade():
    op.add_column('practice_sessions',
                  sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_practice_sessions_user',
                         'practice_sessions', 'users', ['user_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_practice_sessions_user', 'practice_sessions', type_='foreignkey')
    op.drop_column('practice_sessions', 'user_id')
```

### 5. Implement Query Optimization

```python
# Add query optimization utilities
class QueryOptimizer:
    @staticmethod
    def optimize_user_vocabulary_query(user_id, category_id=None):
        query = UserVocabulary.query.filter_by(user_id=user_id)

        if category_id:
            query = query.join(Word).filter(Word.category_id == category_id)

        return query.options(
            joinedload(UserVocabulary.word).joinedload(Word.category)
        )
```

## Implementation Steps

### Phase 1: Schema Fixes (3 days)

1. **Add Missing Foreign Keys** (1 day)
   - Add user_id to practice_sessions
   - Add proper cascade rules
   - Update existing data

2. **Add Missing Indexes** (1 day)
   - Apply performance_indexes.sql
   - Add composite indexes
   - Optimize for common queries

3. **Add Constraints** (1 day)
   - Add unique constraints
   - Add check constraints
   - Add not null constraints

### Phase 2: Query Optimization (5 days)

1. **Fix N+1 Queries** (2 days)
   - Implement eager loading
   - Add query optimization utilities
   - Update all endpoints

2. **Add Pagination** (2 days)
   - Implement pagination for all list endpoints
   - Add sorting options
   - Add filtering capabilities

3. **Add Caching** (1 day)
   - Cache frequently accessed data
   - Implement query result caching
   - Add cache invalidation

### Phase 3: Performance Monitoring (2 days)

1. **Add Query Monitoring** (1 day)
   - Monitor slow queries
   - Add query performance metrics
   - Set up alerts

2. **Database Maintenance** (1 day)
   - Regular vacuum operations
   - Index maintenance
   - Statistics updates

## Database Migration Script

```python
# migrations/fix_database_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add user_id to practice_sessions
    op.add_column('practice_sessions',
                  sa.Column('user_id', sa.Integer(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key('fk_practice_sessions_user',
                         'practice_sessions', 'users', ['user_id'], ['id'])

    # Add missing indexes
    op.create_index('idx_practice_sessions_user_date',
                   'practice_sessions', ['user_id', 'session_date'])
    op.create_index('idx_user_vocabulary_user_mastery',
                   'user_vocabulary', ['user_id', 'mastery_level'])

    # Add unique constraints
    op.create_unique_constraint('unique_user_word',
                              'user_vocabulary', ['user_id', 'word_id'])

def downgrade():
    op.drop_constraint('unique_user_word', 'user_vocabulary', type_='unique')
    op.drop_index('idx_user_vocabulary_user_mastery', 'user_vocabulary')
    op.drop_index('idx_practice_sessions_user_date', 'practice_sessions')
    op.drop_constraint('fk_practice_sessions_user', 'practice_sessions', type_='foreignkey')
    op.drop_column('practice_sessions', 'user_id')
```

## Success Metrics

- **Query Performance**: Reduce average query time from 500ms to <50ms
- **Data Integrity**: 100% foreign key constraint compliance
- **Scalability**: Support 10x more concurrent users
- **Maintenance**: Reduce database maintenance time by 80%

## Priority: HIGH

**Estimated Time**: 2 weeks for complete database optimization
**Business Impact**: Critical for application performance and data integrity
