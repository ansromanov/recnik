import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './SettingsPage.css';

function SettingsPage() {
    const [apiKey, setApiKey] = useState('');
    const [showApiKey, setShowApiKey] = useState(false);
    const [autoAdvanceEnabled, setAutoAdvanceEnabled] = useState(false);
    const [autoAdvanceTimeout, setAutoAdvanceTimeout] = useState(3);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const response = await apiService.getSettings();
            if (response.data.settings) {
                const settings = response.data.settings;
                if (settings.openai_api_key) {
                    setApiKey(settings.openai_api_key);
                }
                setAutoAdvanceEnabled(settings.auto_advance_enabled || false);
                setAutoAdvanceTimeout(settings.auto_advance_timeout || 3);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            setMessage({ type: 'error', text: 'Failed to load settings' });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setMessage({ type: '', text: '' });

            await apiService.updateSettings({
                openai_api_key: apiKey,
                auto_advance_enabled: autoAdvanceEnabled,
                auto_advance_timeout: autoAdvanceTimeout
            });
            setMessage({ type: 'success', text: 'Settings saved successfully!' });

            // Clear success message after 3 seconds
            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } catch (error) {
            console.error('Error saving settings:', error);
            setMessage({ type: 'error', text: 'Failed to save settings' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return <div className="settings-page"><div className="loading">Loading settings...</div></div>;
    }

    return (
        <div className="settings-page">
            <h1>Settings</h1>

            <div className="settings-section">
                <h2>OpenAI API Configuration</h2>
                <p className="settings-description">
                    To use features like vocabulary extraction from news articles and text processing,
                    you need to configure your OpenAI API key. You can get one from{' '}
                    <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">
                        OpenAI's platform
                    </a>.
                </p>

                <div className="api-key-section">
                    <label htmlFor="api-key">OpenAI API Key:</label>
                    <div className="api-key-input-group">
                        <input
                            id="api-key"
                            type={showApiKey ? 'text' : 'password'}
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="sk-..."
                            className="api-key-input"
                        />
                        <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="toggle-visibility-btn"
                        >
                            {showApiKey ? 'Hide' : 'Show'}
                        </button>
                    </div>

                    <div className="settings-info">
                        <p>Your API key is stored securely and is only used for:</p>
                        <ul>
                            <li>Extracting vocabulary from Serbian news articles</li>
                            <li>Processing text to identify Serbian words and their translations</li>
                            <li>Generating example sentences for practice</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div className="settings-section">
                <h2>Practice Settings</h2>
                <p className="settings-description">
                    Configure how the practice session behaves to optimize your learning experience.
                </p>

                <div className="practice-settings-section">
                    <div className="setting-item">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={autoAdvanceEnabled}
                                onChange={(e) => setAutoAdvanceEnabled(e.target.checked)}
                                className="checkbox-input"
                            />
                            <span className="checkbox-text">
                                Auto-advance to next word after answer
                            </span>
                        </label>
                        <p className="setting-description">
                            Automatically move to the next word after a short delay when you answer correctly or incorrectly.
                        </p>
                    </div>

                    {autoAdvanceEnabled && (
                        <div className="setting-item">
                            <label htmlFor="timeout-setting">Auto-advance timeout (seconds):</label>
                            <div className="timeout-input-group">
                                <input
                                    id="timeout-setting"
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={autoAdvanceTimeout}
                                    onChange={(e) => setAutoAdvanceTimeout(parseInt(e.target.value))}
                                    className="timeout-slider"
                                />
                                <span className="timeout-value">{autoAdvanceTimeout}s</span>
                            </div>
                            <p className="setting-description">
                                How long to wait before automatically advancing to the next word.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            <div className="settings-actions">
                {message.text && (
                    <div className={`message ${message.type}`}>
                        {message.text}
                    </div>
                )}

                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="save-button"
                >
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
            </div>

            <div className="settings-section">
                <h2>About</h2>
                <p>
                    Serbian Vocabulary App helps you learn Serbian by reading news articles,
                    extracting vocabulary, and practicing with interactive exercises.
                </p>
            </div>
        </div>
    );
}

export default SettingsPage;
