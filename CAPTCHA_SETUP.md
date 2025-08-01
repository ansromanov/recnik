# CAPTCHA Setup Guide

This guide explains how to set up reCAPTCHA for the Serbian Vocabulary App to protect login and registration forms from abuse.

## Overview

The application supports Google reCAPTCHA v2 for both login and registration endpoints. CAPTCHA verification is optional and can be enabled by configuring the appropriate environment variables.

## Features

- ✅ reCAPTCHA v2 integration
- ✅ Automatic enable/disable based on configuration
- ✅ Server-side verification with detailed error handling
- ✅ Client-side validation and user-friendly error messages
- ✅ CAPTCHA reset when switching between login/register modes
- ✅ Responsive design with proper styling

## Setup Instructions

### 1. Get reCAPTCHA Keys

1. Go to [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click "Create" to add a new site
3. Choose reCAPTCHA v2 with "I'm not a robot" checkbox
4. Add your domains (e.g., `localhost`, `yourdomain.com`)
5. Copy the Site Key and Secret Key

### 2. Configure Environment Variables

Add the following to your `.env` file in the backend directory:

```bash
# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY=your-site-key-here
RECAPTCHA_SECRET_KEY=your-secret-key-here
```

**Important Notes:**

- If either key is missing or empty, CAPTCHA will be automatically disabled
- The site key is public and sent to the frontend
- The secret key is private and used only on the backend for verification

### 3. Install Frontend Dependencies

The frontend requires the `react-google-recaptcha` package:

```bash
cd frontend
npm install react-google-recaptcha
```

### 4. Test the Implementation

1. Start the backend and frontend servers
2. Navigate to the login/register page
3. If CAPTCHA is configured, you should see the reCAPTCHA widget
4. Try submitting without completing CAPTCHA (should show validation error)
5. Complete CAPTCHA and submit (should work normally)

## Development vs Production

### Development

- Use `localhost` as the domain in reCAPTCHA configuration
- CAPTCHA can be disabled by leaving environment variables empty

### Production

- Add your production domain to reCAPTCHA settings
- Always enable CAPTCHA in production environments
- Consider using reCAPTCHA v3 for better user experience (requires code changes)

## Troubleshooting

### CAPTCHA Not Showing

- Check that both `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` are set
- Verify the site key is correct
- Check browser console for JavaScript errors
- Ensure domain is registered in reCAPTCHA console

### CAPTCHA Validation Failing

- Verify the secret key is correct
- Check backend logs for detailed error messages
- Ensure the frontend is sending the CAPTCHA response
- Check network connectivity to Google's servers

### Common Error Messages

- "CAPTCHA response is required" - User didn't complete CAPTCHA
- "CAPTCHA verification failed" - Invalid response or expired token
- "Please complete the CAPTCHA verification" - Frontend validation error

## API Endpoints

### Get CAPTCHA Configuration

```
GET /api/captcha/site-key
```

Returns:

```json
{
  "site_key": "your-site-key",
  "captcha_enabled": true
}
```

### Login with CAPTCHA

```
POST /api/auth/login
{
  "username": "user",
  "password": "pass",
  "captcha_response": "captcha-token"
}
```

### Register with CAPTCHA

```
POST /api/auth/register
{
  "username": "user",
  "password": "pass",
  "captcha_response": "captcha-token"
}
```

## Security Considerations

1. **Always verify CAPTCHA server-side** - Never trust client-side validation alone
2. **Use HTTPS in production** - reCAPTCHA requires secure connections
3. **Rate limiting** - Consider additional rate limiting for auth endpoints
4. **Log failed attempts** - Monitor and log suspicious activity
5. **Keep keys secure** - Never commit keys to version control

## Customization

### Changing CAPTCHA Theme

The reCAPTCHA component supports theme customization:

```jsx
<ReCAPTCHA
  theme="dark"  // or "light"
  size="compact"  // or "normal"
  // ... other props
/>
```

### Custom Error Messages

Error messages can be customized in the `captcha_service.py` file in the `_get_error_message` method.

### Styling

CAPTCHA styling can be modified in `LoginPage.css` under the `.captcha-group` class.

## Future Enhancements

- Upgrade to reCAPTCHA v3 for invisible verification
- Add CAPTCHA to other sensitive endpoints
- Implement fallback CAPTCHA providers
- Add analytics for CAPTCHA success/failure rates
