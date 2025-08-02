/**
 * Sound Service for Practice Games
 * Handles playing correct/incorrect answer sounds with user preferences
 */

class SoundService {
    constructor() {
        this.audioContext = null;
        this.sounds = {
            correct: null,
            incorrect: null
        };
        this.isEnabled = true;
        this.isInitialized = false;

        // Initialize Web Audio API when user interacts
        this.initializeAudio();
    }

    /**
     * Initialize Web Audio API
     */
    async initializeAudio() {
        try {
            // Create AudioContext (requires user interaction)
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();

            // Generate sounds
            this.generateSounds();
            this.isInitialized = true;
        } catch (error) {
            console.warn('Could not initialize audio context:', error);
            this.isInitialized = false;
        }
    }

    /**
     * Generate correct and incorrect sounds using Web Audio API
     */
    generateSounds() {
        if (!this.audioContext) return;

        // Generate correct sound (pleasant chime)
        this.sounds.correct = this.createCorrectSound();

        // Generate incorrect sound (gentle buzz)
        this.sounds.incorrect = this.createIncorrectSound();
    }

    /**
     * Create a pleasant correct answer sound
     */
    createCorrectSound() {
        const duration = 0.3;
        const sampleRate = this.audioContext.sampleRate;
        const frameCount = duration * sampleRate;
        const buffer = this.audioContext.createBuffer(1, frameCount, sampleRate);
        const channelData = buffer.getChannelData(0);

        // Create ascending chime (C-E-G chord progression)
        const frequencies = [523.25, 659.25, 783.99]; // C5, E5, G5

        for (let i = 0; i < frameCount; i++) {
            const t = i / sampleRate;
            let sample = 0;

            frequencies.forEach((freq, index) => {
                const noteStart = (index * duration) / frequencies.length;
                const noteEnd = ((index + 1) * duration) / frequencies.length;

                if (t >= noteStart && t < noteEnd) {
                    // Sine wave with envelope
                    const envelope = Math.exp(-t * 5) * (1 - t / duration);
                    sample += Math.sin(2 * Math.PI * freq * t) * envelope * 0.3;
                }
            });

            channelData[i] = sample;
        }

        return buffer;
    }

    /**
     * Create a gentle incorrect answer sound
     */
    createIncorrectSound() {
        const duration = 0.4;
        const sampleRate = this.audioContext.sampleRate;
        const frameCount = duration * sampleRate;
        const buffer = this.audioContext.createBuffer(1, frameCount, sampleRate);
        const channelData = buffer.getChannelData(0);

        // Create descending tone (A-F progression)
        const startFreq = 440; // A4
        const endFreq = 349.23; // F4

        for (let i = 0; i < frameCount; i++) {
            const t = i / sampleRate;
            const progress = t / duration;

            // Frequency slides down
            const freq = startFreq + (endFreq - startFreq) * progress;

            // Envelope with gentle fade
            const envelope = Math.exp(-t * 3) * (1 - progress * 0.8);

            // Add slight tremolo for texture
            const tremolo = 1 + 0.1 * Math.sin(2 * Math.PI * 6 * t);

            channelData[i] = Math.sin(2 * Math.PI * freq * t) * envelope * tremolo * 0.25;
        }

        return buffer;
    }

    /**
     * Play correct answer sound
     */
    async playCorrect() {
        if (!this.isEnabled || !this.isInitialized) return;

        try {
            await this.ensureAudioContext();
            this.playBuffer(this.sounds.correct);
        } catch (error) {
            console.warn('Could not play correct sound:', error);
        }
    }

    /**
     * Play incorrect answer sound
     */
    async playIncorrect() {
        if (!this.isEnabled || !this.isInitialized) return;

        try {
            await this.ensureAudioContext();
            this.playBuffer(this.sounds.incorrect);
        } catch (error) {
            console.warn('Could not play incorrect sound:', error);
        }
    }

    /**
     * Ensure AudioContext is running
     */
    async ensureAudioContext() {
        if (!this.audioContext) {
            await this.initializeAudio();
        }

        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
    }

    /**
     * Play an audio buffer
     */
    playBuffer(buffer) {
        if (!buffer || !this.audioContext) return;

        const source = this.audioContext.createBufferSource();
        const gainNode = this.audioContext.createGain();

        source.buffer = buffer;
        source.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        // Set volume
        gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);

        source.start();
    }

    /**
     * Enable or disable sounds
     */
    setEnabled(enabled) {
        this.isEnabled = enabled;
    }

    /**
     * Get current enabled state
     */
    getEnabled() {
        return this.isEnabled;
    }

    /**
     * Initialize audio on first user interaction (required by browsers)
     */
    async initializeOnUserInteraction() {
        if (!this.isInitialized) {
            await this.initializeAudio();
        }
    }

    /**
     * Test sounds (for settings page)
     */
    async testCorrectSound() {
        const wasEnabled = this.isEnabled;
        this.setEnabled(true);
        await this.playCorrect();
        this.setEnabled(wasEnabled);
    }

    async testIncorrectSound() {
        const wasEnabled = this.isEnabled;
        this.setEnabled(true);
        await this.playIncorrect();
        this.setEnabled(wasEnabled);
    }
}

// Create singleton instance
const soundService = new SoundService();

export default soundService;
