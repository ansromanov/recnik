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
            console.log('Available env vars:', Object.keys(process.env).filter(key => key.startsWith('REACT_APP_')));
            return;
        }

        console.log('Loading ResponsiveVoice script with API key:', apiKey.substring(0, 4) + '***');

        // Create and load script
        const script = document.createElement('script');
        script.src = `https://code.responsivevoice.org/responsivevoice.js?key=${apiKey}`;
        script.async = true;
        script.onload = () => {
            console.log('ResponsiveVoice script loaded successfully');
            this.scriptLoaded = true;
            // Wait a bit for ResponsiveVoice to initialize completely
            setTimeout(() => this.initialize(), 100);
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

        console.log(`🎤 Setting voice from '${this.currentVoice}' to '${voice}'`);
        console.log(`Voice exists in available list: ${voiceExists}`);
        console.log('Available voices:', availableVoices.map(v => v.id));

        if (voiceExists) {
            const oldVoice = this.currentVoice;
            this.currentVoice = voice;
            console.log(`✅ Voice changed: ${oldVoice} -> ${this.currentVoice}`);
        } else {
            console.warn(`❌ Voice '${voice}' not found. Using default voice '${this.currentVoice}'`);
            console.log('Available voices were:', availableVoices.map(v => v.id));
        }
    }

    /**
     * Get current voice
     */
    getCurrentVoice() {
        return this.currentVoice;
    }

    /**
     * Get available Serbian voices (male and female)
     */
    getAvailableVoices() {
        return [
            { id: 'Serbian Male', name: 'Serbian Male', language: 'sr', gender: 'male' },
            { id: 'Croatian Male', name: 'Croatian Male', language: 'hr', gender: 'male' },
            { id: 'Bosnian Male', name: 'Bosnian Male', language: 'bs', gender: 'male' },
            { id: 'Croatian Female', name: 'Croatian Female', language: 'hr', gender: 'female' },
            { id: 'Bosnian Female', name: 'Bosnian Female', language: 'bs', gender: 'female' }
        ];
    }

    /**
     * Get a voice for a specific speaker in dialog
     * For dialogs, use Serbian Male and Croatian Male to create distinct speakers
     */
    getVoiceForSpeaker(speakerName, speakerIndex = 0) {
        const voices = this.getAvailableVoices();

        // For dialog, we specifically want Serbian Male and Croatian Male
        const dialogVoices = ['Serbian Male', 'Croatian Male'];

        // Assign voices based on speaker characteristics
        const femaleNames = ['Ana', 'Milica', 'Jovana', 'Marija', 'Tamara', 'Teodora', 'Nina', 'Ivana', 'Jelena', 'Sara'];
        const maleNames = ['Marko', 'Stefan', 'Nikola', 'Miloš', 'Aleksandar', 'Filip', 'Luka', 'Petar', 'Nemanja', 'Jovan'];

        // Determine gender based on name
        let isFemale = false;
        if (speakerName) {
            isFemale = femaleNames.includes(speakerName);
        }

        // For female speakers, use female voices if available, otherwise fallback to male dialog voices
        if (isFemale) {
            const femaleVoices = voices.filter(v => v.gender === 'female');
            if (femaleVoices.length > 0) {
                return femaleVoices[speakerIndex % femaleVoices.length].id;
            }
        }

        // For male speakers or fallback, use the dialog voices (Serbian Male, Croatian Male)
        return dialogVoices[speakerIndex % dialogVoices.length];
    }

    /**
     * Get a consistent voice assignment for dialog speakers
     * This ensures the same speaker always gets the same voice within a dialog
     */
    getVoiceForDialogSpeaker(speakerName, allSpeakers = []) {
        // Create a consistent mapping for this dialog session
        const dialogVoices = ['Serbian Male', 'Croatian Male'];

        // Find the index of this speaker in the list of all speakers
        const speakerIndex = allSpeakers.indexOf(speakerName);

        // If speaker not found, use hash of speaker name for consistency
        const index = speakerIndex >= 0 ? speakerIndex : this.hashString(speakerName) % dialogVoices.length;

        return dialogVoices[index % dialogVoices.length];
    }

    /**
     * Simple hash function for consistent speaker voice assignment
     */
    hashString(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }

    /**
     * Play multiple dialog lines with different voices sequentially
     */
    async playDialogWithVoices(dialogLines, allSpeakers = [], options = {}) {
        if (!this.isReady() || !this.isEnabled || !dialogLines || dialogLines.length === 0) {
            console.warn('TTS not ready, disabled, or no dialog lines provided');
            return Promise.resolve();
        }

        const originalVoice = this.getCurrentVoice();
        console.log('Starting dialog playback with', dialogLines.length, 'lines');
        console.log('All speakers:', allSpeakers);
        console.log('Original voice:', originalVoice);

        try {
            for (let i = 0; i < dialogLines.length; i++) {
                const line = dialogLines[i];
                const { speaker, text } = line;

                // Get appropriate voice for this speaker
                const voiceForSpeaker = this.getVoiceForDialogSpeaker(speaker, allSpeakers);
                console.log(`Line ${i + 1}: Speaker "${speaker}" -> Voice "${voiceForSpeaker}"`);

                // Set voice for this speaker
                this.setVoice(voiceForSpeaker);
                console.log(`Current voice set to: ${this.getCurrentVoice()}`);

                // Verify voice was actually changed
                if (window.responsiveVoice) {
                    console.log('ResponsiveVoice available voices:', window.responsiveVoice.getVoices());
                }

                // Play this line and wait for it to finish
                await new Promise((resolve, reject) => {
                    // Force ResponsiveVoice to cancel any ongoing speech before starting new one
                    if (window.responsiveVoice && window.responsiveVoice.isPlaying()) {
                        window.responsiveVoice.cancel();
                        // Small delay to ensure cancellation is complete
                        setTimeout(() => {
                            this.speak(text, {
                                rate: options.rate || 0.8,
                                onstart: () => {
                                    console.log(`▶️ Started playing line ${i + 1}/${dialogLines.length} - ${speaker}: "${text.substring(0, 30)}..." using voice ${voiceForSpeaker}`);
                                    if (options.onlinestart) options.onlinestart(i, speaker, voiceForSpeaker);
                                },
                                onend: () => {
                                    console.log(`✅ Finished line ${i + 1}/${dialogLines.length} - ${speaker}`);
                                    if (options.onlineend) options.onlineend(i, speaker);
                                    resolve();
                                },
                                onerror: (error) => {
                                    console.error(`❌ Error playing line ${i + 1} - ${speaker}:`, error);
                                    if (options.onlineerror) options.onlineerror(i, speaker, error);
                                    reject(error);
                                }
                            });
                        }, 100);
                    } else {
                        this.speak(text, {
                            rate: options.rate || 0.8,
                            onstart: () => {
                                console.log(`▶️ Started playing line ${i + 1}/${dialogLines.length} - ${speaker}: "${text.substring(0, 30)}..." using voice ${voiceForSpeaker}`);
                                if (options.onlinestart) options.onlinestart(i, speaker, voiceForSpeaker);
                            },
                            onend: () => {
                                console.log(`✅ Finished line ${i + 1}/${dialogLines.length} - ${speaker}`);
                                if (options.onlineend) options.onlineend(i, speaker);
                                resolve();
                            },
                            onerror: (error) => {
                                console.error(`❌ Error playing line ${i + 1} - ${speaker}:`, error);
                                if (options.onlineerror) options.onlineerror(i, speaker, error);
                                reject(error);
                            }
                        });
                    }
                });

                // Small pause between speakers for natural flow
                if (i < dialogLines.length - 1) {
                    console.log(`⏸️ Pausing 500ms before next speaker...`);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }

            // All lines completed successfully
            console.log('🎉 All dialog lines completed successfully');
            if (options.onend) options.onend();

        } catch (error) {
            console.error('Error playing dialog:', error);
            if (options.onerror) options.onerror(error);
            throw error;
        } finally {
            // Restore original voice
            console.log(`🔄 Restoring original voice: ${originalVoice}`);
            this.setVoice(originalVoice);
        }
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
