import { useState, useEffect, useCallback } from 'react';
import ttsService from '../services/ttsService';

/**
 * Custom hook for TTS audio functionality
 * Provides easy-to-use audio controls for React components
 */
export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentVoice, setCurrentVoice] = useState('Serbian Male');
    const [isEnabled, setIsEnabled] = useState(true);
    const [isReady, setIsReady] = useState(false);

    // Initialize TTS service state
    useEffect(() => {
        const checkTTSReady = () => {
            setIsReady(ttsService.isReady());
            setIsEnabled(ttsService.getEnabled());
            setCurrentVoice(ttsService.getCurrentVoice());
        };

        // Check immediately
        checkTTSReady();

        // Check periodically until ready
        const interval = setInterval(() => {
            if (!ttsService.isReady()) {
                checkTTSReady();
            } else {
                clearInterval(interval);
            }
        }, 100);

        return () => clearInterval(interval);
    }, []);

    // Monitor playing state
    useEffect(() => {
        const checkPlayingState = () => {
            setIsPlaying(ttsService.getPlaying());
        };

        const interval = setInterval(checkPlayingState, 100);
        return () => clearInterval(interval);
    }, []);

    /**
     * Play audio for Serbian text
     */
    const playAudio = useCallback(async (text, options = {}) => {
        if (!text || !isReady || !isEnabled) return;

        try {
            setIsPlaying(true);
            await ttsService.speak(text, {
                ...options,
                onend: () => {
                    setIsPlaying(false);
                    if (options.onend) options.onend();
                },
                onerror: (error) => {
                    setIsPlaying(false);
                    if (options.onerror) options.onerror(error);
                }
            });
        } catch (error) {
            setIsPlaying(false);
            console.error('Error playing audio:', error);
        }
    }, [isReady, isEnabled]);

    /**
     * Play pronunciation for vocabulary word
     */
    const playPronunciation = useCallback(async (serbianWord, options = {}) => {
        if (!serbianWord || !isReady || !isEnabled) return;

        try {
            setIsPlaying(true);
            await ttsService.playPronunciation(serbianWord, {
                ...options,
                onend: () => {
                    setIsPlaying(false);
                    if (options.onend) options.onend();
                },
                onerror: (error) => {
                    setIsPlaying(false);
                    if (options.onerror) options.onerror(error);
                }
            });
        } catch (error) {
            setIsPlaying(false);
            console.error('Error playing pronunciation:', error);
        }
    }, [isReady, isEnabled]);

    /**
     * Stop current audio
     */
    const stopAudio = useCallback(() => {
        ttsService.stop();
        setIsPlaying(false);
    }, []);

    /**
     * Change voice preference
     */
    const changeVoice = useCallback((voice) => {
        ttsService.setVoice(voice);
        setCurrentVoice(voice);
    }, []);

    /**
     * Toggle audio enabled state
     */
    const toggleEnabled = useCallback(() => {
        const newEnabled = !isEnabled;
        ttsService.setEnabled(newEnabled);
        setIsEnabled(newEnabled);
        if (!newEnabled) {
            stopAudio();
        }
    }, [isEnabled, stopAudio]);

    /**
     * Set audio enabled state
     */
    const setAudioEnabled = useCallback((enabled) => {
        ttsService.setEnabled(enabled);
        setIsEnabled(enabled);
        if (!enabled) {
            stopAudio();
        }
    }, [stopAudio]);

    /**
     * Get available voices
     */
    const getAvailableVoices = useCallback(() => {
        return ttsService.getAvailableVoices();
    }, []);

    /**
     * Test TTS functionality
     */
    const testTTS = useCallback(async () => {
        try {
            return await ttsService.testTTS();
        } catch (error) {
            console.error('Error testing TTS:', error);
            return false;
        }
    }, []);

    /**
     * Get TTS status for debugging
     */
    const getTTSStatus = useCallback(() => {
        return ttsService.getStatus();
    }, []);

    return {
        // State
        isPlaying,
        currentVoice,
        isEnabled,
        isReady,

        // Actions
        playAudio,
        playPronunciation,
        stopAudio,
        changeVoice,
        toggleEnabled,
        setAudioEnabled,

        // Utilities
        getAvailableVoices,
        testTTS,
        getTTSStatus
    };
};

export default useAudio;
