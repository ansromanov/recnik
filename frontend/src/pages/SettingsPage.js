import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './SettingsPage.css';

function SettingsPage() {
    const [apiKey, setApiKey] = useState('');
    const [showApiKey, setShowApiKey] = useState(false);
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
            if (response.data.settings && response.data.settings.openai_api_key) {
                setApiKey(response.data.settings.openai_api_key);
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

            await apiService.updateSettings({ openai_api_key: apiKey });
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

                    {message.text && (
                        <div className={`message ${message.type}`}>
                            {message.text}
                        </div>
                    )}

                    <button
                        onClick={handleSave}
                        disabled={saving || !apiKey.trim()}
                        className="save-button"
                    >
                        {saving ? 'Saving...' : 'Save Settings'}
                    </button>
                </div>
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
