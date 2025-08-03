import { useEffect, useCallback } from 'react';
import { useAudio } from './useAudio';
import settingsService from '../services/settingsService';

/**
 * Custom hook for auto-playing voice when vocabulary words are displayed
 * Automatically plays pronunciation based on user settings
 */
export const useAutoPlayVoice = () => {
    const { playPronunciation, isReady, isEnabled } = useAudio();

    /**
     * Auto-play pronunciation for a Serbian word if setting is enabled
     */
    const autoPlayWord = useCallback(async (serbianWord, delay = 500) => {
        if (!serbianWord || !isReady || !isEnabled) return;

        // Check if auto-play is enabled in settings
        const isAutoPlayEnabled = settingsService.isAutoPlayVoiceEnabled();
        if (!isAutoPlayEnabled) return;

        try {
            // Add a small delay to prevent immediate playback conflicts
            setTimeout(async () => {
                await playPronunciation(serbianWord, {
                    rate: 0.7, // Slightly slower for learning
                    onstart: () => {
                        console.log(`Auto-playing pronunciation: ${serbianWord}`);
                    },
                    onerror: (error) => {
                        console.warn('Auto-play pronunciation failed:', error);
                    }
                });
            }, delay);
        } catch (error) {
            console.warn('Auto-play pronunciation error:', error);
        }
    }, [playPronunciation, isReady, isEnabled]);

    /**
     * Auto-play multiple words in sequence
     */
    const autoPlayWords = useCallback(async (words, delayBetween = 1000) => {
        if (!words || !Array.isArray(words) || words.length === 0) return;

        const isAutoPlayEnabled = settingsService.isAutoPlayVoiceEnabled();
        if (!isAutoPlayEnabled) return;

        for (let i = 0; i < words.length; i++) {
            if (words[i]) {
                await autoPlayWord(words[i], i * delayBetween);
            }
        }
    }, [autoPlayWord]);

    /**
     * Check if auto-play is currently enabled
     */
    const isAutoPlayEnabled = useCallback(() => {
        return settingsService.isAutoPlayVoiceEnabled() && isReady && isEnabled;
    }, [isReady, isEnabled]);

    return {
        autoPlayWord,
        autoPlayWords,
        isAutoPlayEnabled
    };
};

export default useAutoPlayVoice;
