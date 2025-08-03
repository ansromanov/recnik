/**
 * Text-to-Speech Service using ResponsiveVoice.js
 * Handles Serbian pronunciation for vocabulary words
 */

class TTSService {
    constructor() {
        this.isInitialized = false;
        this.currentVoice = 'Serbian Male';
        this.isPlaying = false;
        this.audioQueue = [];
        this.isEnabled = true;
        this.scriptLoaded = false;

        // Load ResponsiveVoice script and initialize
        this.loadResponsiveVoiceScript();
    }

    /**
     * Load ResponsiveVoice.js script dynamically with API key from environment
     */
    loadResponsiveVoiceScript() {
        // Check if script is already loaded
        if (typeof window.responsiveVoice !== 'undefined') {
            this.scriptLoaded = true;
            this.initialize();
            return;
        }

        // Get API key from environment variable
        const apiKey = process.env.REACT_APP_RESPONSIVEVOICE_API_KEY;

        if (!apiKey) {
            console.error('REACT_APP_RESPONSIVEVOICE_API_KEY environment variable is not set');
            return;
        }

        // Create and load script
        const script = document.createElement('script');
        script.src = `https://code.responsivevoice.org/responsivevoice.js?key=${apiKey}`;
        script.async = true;
        script.onload = () => {
            this.scriptLoaded = true;
            this.initialize();
        };
        script.onerror = (error) => {
            console.error('Failed to load ResponsiveVoice script:', error);
        };

        document.head.appendChild(script);
    }

    /**
     * Initialize ResponsiveVoice.js
     */
    initialize() {
        // Check if ResponsiveVoice is loaded
        if (typeof window.responsiveVoice !== 'undefined') {
            this.isInitialized = true;
            console.log('TTS Service initialized with ResponsiveVoice.js');
        } else {
            // Retry initialization after a short delay
            setTimeout(() => this.initialize(), 100);
        }
    }

    /**
     * Check if TTS is available and ready
     */
    isReady() {
        return this.isInitialized && typeof window.responsiveVoice !== 'undefined';
    }

    /**
     * Speak Serbian text
     */
    async speak(text, options = {}) {
        if (!this.isReady() || !this.isEnabled || !text) {
            console.warn('TTS not ready, disabled, or no text provided');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                const defaultOptions = {
                    rate: 0.8,
                    pitch: 1,
                    volume: 1,
                    onstart: () => {
                        this.isPlaying = true;
                        if (options.onstart) options.onstart();
                    },
                    onend: () => {
                        this.isPlaying = false;
                        if (options.onend) options.onend();
                        resolve();
                    },
                    onerror: (error) => {
                        this.isPlaying = false;
                        console.error('TTS Error:', error);
                        if (options.onerror) options.onerror(error);
                        reject(error);
                    }
                };

                const finalOptions = { ...defaultOptions, ...options };

                // Validate voice exists before speaking
                const availableVoices = this.getAvailableVoices();
                const voiceExists = availableVoices.some(v => v.id === this.currentVoice);

                if (!voiceExists) {
                    console.warn(`Current voice '${this.currentVoice}' not available. Falling back to 'Serbian Male'`);
                    this.currentVoice = 'Serbian Male';
                }

                window.responsiveVoice.speak(text, this.currentVoice, finalOptions);
            } catch (error) {
                this.isPlaying = false;
                console.error('TTS Speak Error:', error);
                reject(error);
            }
        });
    }

    /**
     * Stop current speech
     */
    stop() {
        if (this.isReady()) {
            window.responsiveVoice.cancel();
            this.isPlaying = false;
        }
    }

    /**
     * Set voice preference with validation
     */
    setVoice(voice) {
        const availableVoices = this.getAvailableVoices();
        const voiceExists = availableVoices.some(v => v.id === voice);

        if (voiceExists) {
            this.currentVoice = voice;
        } else {
            console.warn(`Voice '${voice}' not found. Using default voice '${this.currentVoice}'`);
        }
    }

    /**
     * Get current voice
     */
    getCurrentVoice() {
        return this.currentVoice;
    }

    /**
     * Get available Serbian voices (male only)
     */
    getAvailableVoices() {
        return [
            { id: 'Serbian Male', name: 'Serbian Male', language: 'sr' },
            { id: 'Croatian Male', name: 'Croatian Male', language: 'hr' },
            { id: 'Bosnian Male', name: 'Bosnian Male', language: 'bs' }
        ];
    }

    /**
     * Enable or disable TTS
     */
    setEnabled(enabled) {
        this.isEnabled = enabled;
        if (!enabled) {
            this.stop();
        }
    }

    /**
     * Get enabled state
     */
    getEnabled() {
        return this.isEnabled;
    }

    /**
     * Get playing state
     */
    getPlaying() {
        return this.isPlaying;
    }

    /**
     * Play pronunciation for a Serbian word
     */
    async playPronunciation(serbianWord, options = {}) {
        if (!serbianWord) return;

        try {
            await this.speak(serbianWord, {
                rate: 0.7, // Slightly slower for pronunciation
                ...options
            });
        } catch (error) {
            console.error('Error playing pronunciation:', error);
        }
    }

    /**
     * Play pronunciation with visual feedback
     */
    async playPronunciationWithFeedback(serbianWord, buttonElement, options = {}) {
        if (!serbianWord || !buttonElement) return;

        const originalText = buttonElement.textContent;
        const originalDisabled = buttonElement.disabled;

        try {
            // Update button state
            buttonElement.textContent = '🔊 Playing...';
            buttonElement.disabled = true;

            await this.speak(serbianWord, {
                rate: 0.7,
                onend: () => {
                    // Restore button state
                    buttonElement.textContent = originalText;
                    buttonElement.disabled = originalDisabled;
                    if (options.onend) options.onend();
                },
                onerror: (error) => {
                    // Restore button state on error
                    buttonElement.textContent = originalText;
                    buttonElement.disabled = originalDisabled;
                    if (options.onerror) options.onerror(error);
                },
                ...options
            });
        } catch (error) {
            // Restore button state on error
            buttonElement.textContent = originalText;
            buttonElement.disabled = originalDisabled;
            console.error('Error playing pronunciation with feedback:', error);
        }
    }

    /**
     * Test TTS functionality
     */
    async testTTS() {
        try {
            await this.speak('Zdravo! Ovo je test srpskog izgovora.', {
                rate: 0.8
            });
            return true;
        } catch (error) {
            console.error('TTS test failed:', error);
            return false;
        }
    }

    /**
     * Check if ResponsiveVoice is working
     */
    isResponsiveVoiceWorking() {
        return this.isReady() && window.responsiveVoice.voiceSupport();
    }

    /**
     * Get TTS status for debugging
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isReady: this.isReady(),
            isEnabled: this.isEnabled,
            isPlaying: this.isPlaying,
            currentVoice: this.currentVoice,
            responsiveVoiceAvailable: typeof window.responsiveVoice !== 'undefined',
            voiceSupport: this.isReady() ? window.responsiveVoice.voiceSupport() : false
        };
    }
}

// Create singleton instance
const ttsService = new TTSService();

export default ttsService;
