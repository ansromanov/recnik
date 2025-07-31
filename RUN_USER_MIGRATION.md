# User-Specific Vocabulary Migration Guide

This migration adds user-specific vocabulary tracking to ensure each user has their own vocabulary list and practice statistics.

## What This Migration Does

1. Adds a `user_id` column to the `user_vocabulary` table
2. Adds a `user_id` column to the `practice_sessions` table
3. Creates proper foreign key relationships
4. Updates unique constraints to ensure each user has their own vocabulary
5. Creates indexes for better performance

## Running the Migration

### Option 1: Using Docker Compose (Recommended)

1. Make sure your containers are running:

   ```bash
   docker-compose up -d
   ```

2. Run the migration script inside the backend container:

   ```bash
   docker-compose exec backend python add_user_relationships.py
   ```

### Option 2: Direct Python Execution

If you have the Python environment set up locally:

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Ensure you have the `.env` file with `DATABASE_URL` set

3. Run the migration:

   ```bash
   python add_user_relationships.py
   ```

## Important Notes

- **Existing Data**: If you have existing vocabulary data without user associations, this migration will preserve the data but it won't be associated with any user. You may need to manually assign or re-add words to your vocabulary after logging in.

- **No Downtime**: This migration can be run while the application is running.

- **Idempotent**: The migration is safe to run multiple times - it will only make changes if they haven't been applied yet.

## After Migration

1. All new vocabulary additions will be user-specific
2. Practice sessions will be tracked per user
3. Statistics will show only the logged-in user's data
4. Each user maintains their own progress and mastery levels

## Troubleshooting

If you encounter any issues:

1. Check the migration output for error messages
2. Ensure the database is accessible
3. Verify the `DATABASE_URL` in your `.env` file
4. Check that the `users` table exists (run `add_auth_tables.py` first if needed)

## Rollback (if needed)

To rollback this migration, you would need to:

1. Remove the foreign key constraints
2. Drop the `user_id` columns
3. Restore the original unique constraint on `user_vocabulary`

However, this would result in loss of user-specific associations.
