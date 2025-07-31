# Troubleshooting Guide

## Error: 500 Internal Server Error on Vocabulary/Practice Pages

### Problem

You're getting 500 errors when trying to access vocabulary or practice features.

### Solution

This happens when:

1. You're not logged in (authentication is now required)
2. The database migration hasn't been run

### Steps to Fix

1. **Ensure the migration has been run** (already completed):

   ```bash
   docker-compose exec backend python add_user_relationships.py
   ```

2. **Make sure you're logged in**:
   - Go to the login page
   - Log in with your credentials
   - The app should redirect you to the home page

3. **Configure your OpenAI API key** (required for text processing):
   - After logging in, go to Settings
   - Enter your OpenAI API key
   - Save the settings

## Common Issues

### "401 Unauthorized" Errors

- **Cause**: You're not logged in or your session has expired
- **Fix**: Log in again

### "Please configure your OpenAI API key in settings" Error

- **Cause**: Your user account doesn't have an OpenAI API key configured
- **Fix**: Go to Settings and add your API key

### Empty Vocabulary List

- **Cause**: User-specific vocabulary means each user starts with an empty vocabulary
- **Fix**: Add words by:
  - Using the "Process Text" feature
  - Reading news articles and extracting vocabulary
  - The words you add will be tied to your account only

### No Words Available for Practice

- **Cause**: Practice mode only uses words from your personal vocabulary
- **Fix**:
  1. Add some words to your vocabulary first using "Process Text" or "News" features
  2. Refresh the page after adding words
  3. The practice feature now includes ALL words in your vocabulary (not just low-mastery ones)
  4. Make sure you're logged in as the same user who added the words

## Verification Steps

1. **Check if you're logged in**:
   - Look for your username in the navigation bar
   - If you see "Login" instead, you need to log in

2. **Test the API**:
   - Open browser developer tools (F12)
   - Go to Network tab
   - Try accessing vocabulary
   - Check if requests include `Authorization: Bearer [token]` header

3. **Verify migration status**:
   - The migration output should show "Migration completed successfully!"
   - If you see errors, check the database connection

## Orphaned Vocabulary After Migration

If you had vocabulary before the user-specific migration, those words might not be associated with any user.

### Symptoms

- You see words in the vocabulary page
- Practice mode says "No words available"
- Backend logs show "User X has 0 words in vocabulary"

### Fix

Run this command to assign orphaned vocabulary to your user (replace `1` with your user ID if different):

```bash
docker-compose exec backend python fix_orphaned_vocabulary.py 1
```

## Need More Help?

If you're still having issues:

1. Check the backend logs: `docker-compose logs backend`
2. Restart the containers: `docker-compose restart`
3. Clear your browser's local storage and cookies for localhost:3000
