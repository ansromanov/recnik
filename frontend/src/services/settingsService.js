/**
 * Settings Service for managing global application settings
 * Provides centralized access to user preferences
 */

class SettingsService {
    constructor() {
        this.settings = {
            autoPlayVoice: true,
            soundsEnabled: true,
            autoAdvanceEnabled: false,
            autoAdvanceTimeout: 3,
            masteryThreshold: 5,
            practiceRoundCount: 10
        };
        this.listeners = [];
        this.loadFromLocalStorage();
    }

    /**
     * Load settings from localStorage
     */
    loadFromLocalStorage() {
        try {
            const stored = localStorage.getItem('vocabularyAppSettings');
            if (stored) {
                const parsedSettings = JSON.parse(stored);
                this.settings = { ...this.settings, ...parsedSettings };
            }
        } catch (error) {
            console.warn('Failed to load settings from localStorage:', error);
        }
    }

    /**
     * Save settings to localStorage
     */
    saveToLocalStorage() {
        try {
            localStorage.setItem('vocabularyAppSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('Failed to save settings to localStorage:', error);
        }
    }

    /**
     * Get a specific setting value
     */
    getSetting(key) {
        return this.settings[key];
    }

    /**
     * Set a specific setting value
     */
    setSetting(key, value) {
        const oldValue = this.settings[key];
        this.settings[key] = value;

        // Save to localStorage
        this.saveToLocalStorage();

        // Notify listeners of the change
        this.notifyListeners(key, value, oldValue);
    }

    /**
     * Update multiple settings at once
     */
    updateSettings(newSettings) {
        const changes = {};

        Object.keys(newSettings).forEach(key => {
            if (this.settings.hasOwnProperty(key)) {
                const oldValue = this.settings[key];
                this.settings[key] = newSettings[key];
                changes[key] = { newValue: newSettings[key], oldValue };
            }
        });

        // Save to localStorage
        this.saveToLocalStorage();

        // Notify listeners of all changes
        Object.keys(changes).forEach(key => {
            this.notifyListeners(key, changes[key].newValue, changes[key].oldValue);
        });
    }

    /**
     * Get all settings
     */
    getAllSettings() {
        return { ...this.settings };
    }

    /**
     * Subscribe to setting changes
     */
    subscribe(callback) {
        this.listeners.push(callback);

        // Return unsubscribe function
        return () => {
            this.listeners = this.listeners.filter(listener => listener !== callback);
        };
    }

    /**
     * Notify all listeners of a setting change
     */
    notifyListeners(key, newValue, oldValue) {
        this.listeners.forEach(callback => {
            try {
                callback(key, newValue, oldValue);
            } catch (error) {
                console.error('Error in settings listener:', error);
            }
        });
    }

    /**
     * Check if auto-play voice is enabled
     */
    isAutoPlayVoiceEnabled() {
        return this.settings.autoPlayVoice;
    }

    /**
     * Enable or disable auto-play voice
     */
    setAutoPlayVoice(enabled) {
        this.setSetting('autoPlayVoice', enabled);
    }

    /**
     * Initialize settings from API response
     */
    initializeFromAPI(apiSettings) {
        if (!apiSettings) return;

        const mappedSettings = {
            autoPlayVoice: apiSettings.auto_play_voice !== undefined ? apiSettings.auto_play_voice : true,
            soundsEnabled: apiSettings.sounds_enabled !== undefined ? apiSettings.sounds_enabled : true,
            autoAdvanceEnabled: apiSettings.auto_advance_enabled || false,
            autoAdvanceTimeout: apiSettings.auto_advance_timeout || 3,
            masteryThreshold: apiSettings.mastery_threshold || 5,
            practiceRoundCount: apiSettings.practice_round_count || 10
        };

        this.updateSettings(mappedSettings);
    }
}

// Create singleton instance
const settingsService = new SettingsService();

export default settingsService;
