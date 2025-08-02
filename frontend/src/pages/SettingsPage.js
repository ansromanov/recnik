import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import soundService from '../services/soundService';
import './SettingsPage.css';

function SettingsPage() {
    const [apiKey, setApiKey] = useState('');
    const [showApiKey, setShowApiKey] = useState(false);
    const [autoAdvanceEnabled, setAutoAdvanceEnabled] = useState(false);
    const [autoAdvanceTimeout, setAutoAdvanceTimeout] = useState(3);
    const [masteryThreshold, setMasteryThreshold] = useState(5);
    const [practiceRoundCount, setPracticeRoundCount] = useState(10);
    const [soundsEnabled, setSoundsEnabled] = useState(true);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [contentSources, setContentSources] = useState({});
    const [selectedSources, setSelectedSources] = useState([]);
    const [sourcesLoading, setSourcesLoading] = useState(false);

    // Avatar-related state
    const [currentAvatar, setCurrentAvatar] = useState(null);
    const [avatarStyles, setAvatarStyles] = useState([]);
    const [avatarVariations, setAvatarVariations] = useState([]);
    const [avatarLoading, setAvatarLoading] = useState(false);
    const [showAvatarVariations, setShowAvatarVariations] = useState(false);

    useEffect(() => {
        loadSettings();
        loadContentSources();
        loadCurrentAvatar();
        loadAvatarStyles();
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
                setMasteryThreshold(settings.mastery_threshold || 5);
                setPracticeRoundCount(settings.practice_round_count || 10);
                setSoundsEnabled(settings.sounds_enabled !== undefined ? settings.sounds_enabled : true);

                // Load selected sources from settings
                if (settings.preferred_content_sources) {
                    setSelectedSources(settings.preferred_content_sources);
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            setMessage({ type: 'error', text: 'Failed to load settings' });
        } finally {
            setLoading(false);
        }
    };

    const loadContentSources = async () => {
        try {
            setSourcesLoading(true);
            const response = await apiService.getContentSources();
            if (response.data.sources) {
                setContentSources(response.data.sources);
            }
        } catch (error) {
            console.error('Error loading content sources:', error);
        } finally {
            setSourcesLoading(false);
        }
    };

    const loadCurrentAvatar = async () => {
        try {
            const response = await apiService.getCurrentAvatar();
            setCurrentAvatar(response.data.avatar);
        } catch (error) {
            console.error('Error loading current avatar:', error);
        }
    };

    const loadAvatarStyles = async () => {
        try {
            const response = await apiService.getAvatarStyles();
            setAvatarStyles(response.data.styles);
        } catch (error) {
            console.error('Error loading avatar styles:', error);
        }
    };

    const loadAvatarVariations = async () => {
        try {
            setAvatarLoading(true);
            const response = await apiService.getAvatarVariations(6);
            setAvatarVariations(response.data.variations);
            setShowAvatarVariations(true);
        } catch (error) {
            console.error('Error loading avatar variations:', error);
            setMessage({ type: 'error', text: 'Failed to load avatar variations' });
        } finally {
            setAvatarLoading(false);
        }
    };

    const handleGenerateNewAvatar = async () => {
        try {
            setAvatarLoading(true);
            const response = await apiService.generateAvatar();
            setCurrentAvatar(response.data.avatar);
            setMessage({ type: 'success', text: 'New avatar generated successfully!' });

            // Clear success message after 3 seconds
            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } catch (error) {
            console.error('Error generating avatar:', error);
            setMessage({ type: 'error', text: 'Failed to generate new avatar' });
        } finally {
            setAvatarLoading(false);
        }
    };

    const handleSelectAvatarStyle = async (style, seed) => {
        try {
            setAvatarLoading(true);
            const response = await apiService.selectAvatar(style, seed);
            setCurrentAvatar(response.data.avatar);
            setShowAvatarVariations(false);
            setMessage({ type: 'success', text: `Avatar style "${style}" selected successfully!` });

            // Clear success message after 3 seconds
            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } catch (error) {
            console.error('Error selecting avatar style:', error);
            setMessage({ type: 'error', text: 'Failed to select avatar style' });
        } finally {
            setAvatarLoading(false);
        }
    };

    const handleAvatarUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            setMessage({ type: 'error', text: 'File size too large. Maximum allowed size is 5MB.' });
            return;
        }

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            setMessage({ type: 'error', text: 'Invalid file type. Allowed types: JPEG, PNG, GIF, WebP' });
            return;
        }

        try {
            setAvatarLoading(true);
            const response = await apiService.uploadAvatar(file);
            setCurrentAvatar(response.data.avatar);
            setMessage({ type: 'success', text: 'Avatar uploaded successfully!' });

            // Clear success message after 3 seconds
            setTimeout(() => {
                setMessage({ type: '', text: '' });
            }, 3000);
        } catch (error) {
            console.error('Error uploading avatar:', error);
            setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to upload avatar' });
        } finally {
            setAvatarLoading(false);
        }
    };

    const handleSourceToggle = (sourceKey) => {
        setSelectedSources(prev =>
            prev.includes(sourceKey)
                ? prev.filter(s => s !== sourceKey)
                : [...prev, sourceKey]
        );
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setMessage({ type: '', text: '' });

            await apiService.updateSettings({
                openai_api_key: apiKey,
                auto_advance_enabled: autoAdvanceEnabled,
                auto_advance_timeout: autoAdvanceTimeout,
                mastery_threshold: masteryThreshold,
                practice_round_count: practiceRoundCount,
                sounds_enabled: soundsEnabled,
                preferred_content_sources: selectedSources
            });

            // Update sound service state
            soundService.setEnabled(soundsEnabled);
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
                <h2>Content Sources</h2>
                <p className="settings-description">
                    Select which news sources you want to see in your content feed. This helps customize your learning experience.
                </p>

                {sourcesLoading ? (
                    <div className="loading">Loading sources...</div>
                ) : (
                    <div className="sources-settings-section">
                        {Object.entries(contentSources).filter(([key]) => key !== 'all').map(([key, source]) => (
                            <div key={key} className="setting-item">
                                <label className="checkbox-label">
                                    <input
                                        type="checkbox"
                                        checked={selectedSources.includes(source.value)}
                                        onChange={() => handleSourceToggle(source.value)}
                                        className="checkbox-input"
                                    />
                                    <span className="checkbox-text">
                                        {source.name}
                                    </span>
                                </label>
                                {source.description && (
                                    <p className="setting-description">
                                        {source.description}
                                    </p>
                                )}
                            </div>
                        ))}
                        {Object.keys(contentSources).length === 0 && (
                            <p className="no-sources">No content sources available</p>
                        )}
                    </div>
                )}
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

                    <div className="setting-item">
                        <label htmlFor="practice-round-count">Practice round count (words per session):</label>
                        <div className="timeout-input-group">
                            <input
                                id="practice-round-count"
                                type="range"
                                min="5"
                                max="30"
                                value={practiceRoundCount}
                                onChange={(e) => setPracticeRoundCount(parseInt(e.target.value))}
                                className="timeout-slider"
                            />
                            <span className="timeout-value">{practiceRoundCount}</span>
                        </div>
                        <p className="setting-description">
                            How many words to include in each practice session. Higher values provide longer practice sessions.
                        </p>
                    </div>

                    <div className="setting-item">
                        <label htmlFor="mastery-threshold">Mastery threshold (correct answers needed):</label>
                        <div className="timeout-input-group">
                            <input
                                id="mastery-threshold"
                                type="range"
                                min="3"
                                max="10"
                                value={masteryThreshold}
                                onChange={(e) => setMasteryThreshold(parseInt(e.target.value))}
                                className="timeout-slider"
                            />
                            <span className="timeout-value">{masteryThreshold}</span>
                        </div>
                        <p className="setting-description">
                            How many correct answers are needed to consider a word mastered. Lower values make it easier to master words.
                        </p>
                    </div>

                    <div className="setting-item">
                        <label className="checkbox-label">
                            <input
                                type="checkbox"
                                checked={soundsEnabled}
                                onChange={(e) => setSoundsEnabled(e.target.checked)}
                                className="checkbox-input"
                            />
                            <span className="checkbox-text">
                                Enable practice sounds
                            </span>
                        </label>
                        <p className="setting-description">
                            Play sound effects when you answer questions correctly or incorrectly during practice.
                        </p>

                        {soundsEnabled && (
                            <div className="sound-test-buttons" style={{ marginTop: '10px' }}>
                                <button
                                    type="button"
                                    onClick={() => soundService.testCorrectSound()}
                                    className="btn btn-sm btn-success"
                                    style={{ marginRight: '10px', fontSize: '14px', padding: '6px 12px' }}
                                >
                                    🔊 Test Correct Sound
                                </button>
                                <button
                                    type="button"
                                    onClick={() => soundService.testIncorrectSound()}
                                    className="btn btn-sm btn-danger"
                                    style={{ fontSize: '14px', padding: '6px 12px' }}
                                >
                                    🔊 Test Incorrect Sound
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="settings-section">
                <h2>Avatar Settings</h2>
                <p className="settings-description">
                    Customize your profile avatar. Choose from AI-generated avatars or upload your own image.
                </p>

                <div className="avatar-settings-section">
                    <div className="current-avatar-section">
                        <h3>Current Avatar</h3>
                        <div className="avatar-display">
                            {currentAvatar ? (
                                <img
                                    src={currentAvatar.avatar_url}
                                    alt="Current Avatar"
                                    className="current-avatar-image"
                                    onError={(e) => {
                                        console.error('Avatar failed to load:', currentAvatar.avatar_url);
                                        e.target.style.display = 'none';
                                    }}
                                />
                            ) : (
                                <div className="avatar-placeholder">No Avatar</div>
                            )}
                            <div className="avatar-info">
                                {currentAvatar && (
                                    <div>
                                        <p><strong>Type:</strong> {currentAvatar.avatar_type === 'ai_generated' ? 'AI Generated' : 'Uploaded'}</p>
                                        {currentAvatar.avatar_type === 'ai_generated' && currentAvatar.avatar_seed && (
                                            <p><strong>Style ID:</strong> {currentAvatar.avatar_seed.substring(0, 8)}...</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="avatar-actions">
                        <h3>Change Avatar</h3>
                        <div className="avatar-buttons">
                            <button
                                onClick={handleGenerateNewAvatar}
                                disabled={avatarLoading}
                                className="btn btn-secondary"
                            >
                                {avatarLoading ? 'Generating...' : '🎲 Generate New Avatar'}
                            </button>

                            <button
                                onClick={loadAvatarVariations}
                                disabled={avatarLoading}
                                className="btn btn-secondary"
                            >
                                {avatarLoading ? 'Loading...' : '🎨 Browse Styles'}
                            </button>

                            <div className="avatar-upload-section">
                                <label htmlFor="avatar-upload" className="btn btn-secondary">
                                    📁 Upload Custom Avatar
                                </label>
                                <input
                                    id="avatar-upload"
                                    type="file"
                                    accept="image/*"
                                    onChange={handleAvatarUpload}
                                    style={{ display: 'none' }}
                                />
                                <p className="upload-info">
                                    Max size: 5MB. Supported: JPEG, PNG, GIF, WebP
                                </p>
                            </div>
                        </div>
                    </div>

                    {showAvatarVariations && (
                        <div className="avatar-variations">
                            <h3>Choose a Style</h3>
                            <div className="avatar-grid">
                                {avatarVariations.map((variation, index) => (
                                    <div key={index} className="avatar-option">
                                        <img
                                            src={variation.avatar_url}
                                            alt={variation.style_name}
                                            className="variation-avatar"
                                            onClick={() => handleSelectAvatarStyle(variation.style, avatarVariations[0]?.seed || currentAvatar?.avatar_seed)}
                                        />
                                        <p className="variation-name">{variation.style_name}</p>
                                    </div>
                                ))}
                            </div>
                            <button
                                onClick={() => setShowAvatarVariations(false)}
                                className="btn btn-secondary"
                                style={{ marginTop: '20px' }}
                            >
                                Cancel
                            </button>
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
