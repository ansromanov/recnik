import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReCAPTCHA from 'react-google-recaptcha';
import './LoginPage.css';

function LoginPage({ onLogin }) {
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [captchaEnabled, setCaptchaEnabled] = useState(false);
    const [captchaSiteKey, setCaptchaSiteKey] = useState('');
    const [captchaResponse, setCaptchaResponse] = useState('');
    const navigate = useNavigate();
    const recaptchaRef = useRef(null);

    // Fetch CAPTCHA configuration on component mount
    useEffect(() => {
        const fetchCaptchaConfig = async () => {
            try {
                const response = await fetch('/api/captcha/site-key');
                const data = await response.json();

                if (response.ok) {
                    setCaptchaEnabled(data.captcha_enabled);
                    setCaptchaSiteKey(data.site_key);
                }
            } catch (error) {
                console.error('Error fetching CAPTCHA config:', error);
                // If we can't fetch config, assume CAPTCHA is disabled
                setCaptchaEnabled(false);
            }
        };

        fetchCaptchaConfig();
    }, []);

    const handleCaptchaChange = (response) => {
        setCaptchaResponse(response);
    };

    const handleCaptchaExpired = () => {
        setCaptchaResponse('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Validate CAPTCHA if enabled
        if (captchaEnabled && !captchaResponse) {
            setError('Please complete the CAPTCHA verification');
            return;
        }

        setLoading(true);

        try {
            const endpoint = isLoginMode ? '/api/auth/login' : '/api/auth/register';
            const requestBody = {
                username,
                password,
                ...(captchaEnabled && { captcha_response: captchaResponse })
            };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Authentication failed');
            }

            // Store the token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            // Call parent's onLogin callback
            if (onLogin) {
                onLogin(data.access_token, data.user);
            }

            // Navigate to home page
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-container">
                <h1>{isLoginMode ? 'Login' : 'Register'}</h1>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            type="text"
                            id="username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={loading}
                        />
                    </div>

                    {captchaEnabled && captchaSiteKey && (
                        <div className="form-group captcha-group">
                            <ReCAPTCHA
                                ref={recaptchaRef}
                                sitekey={captchaSiteKey}
                                onChange={handleCaptchaChange}
                                onExpired={handleCaptchaExpired}
                                onErrored={() => setCaptchaResponse('')}
                            />
                        </div>
                    )}

                    <button type="submit" disabled={loading || (captchaEnabled && !captchaResponse)}>
                        {loading ? 'Loading...' : (isLoginMode ? 'Login' : 'Register')}
                    </button>
                </form>

                <p className="toggle-mode">
                    {isLoginMode ? "Don't have an account? " : "Already have an account? "}
                    <button
                        type="button"
                        onClick={() => {
                            setIsLoginMode(!isLoginMode);
                            setError('');
                            // Reset CAPTCHA when switching modes
                            setCaptchaResponse('');
                            if (recaptchaRef.current) {
                                recaptchaRef.current.reset();
                            }
                        }}
                        disabled={loading}
                        className="link-button"
                    >
                        {isLoginMode ? 'Register' : 'Login'}
                    </button>
                </p>
            </div>
        </div>
    );
}

export default LoginPage;
