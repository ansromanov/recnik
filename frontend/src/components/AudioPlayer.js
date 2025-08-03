import React from 'react';
import { useAudio } from '../hooks/useAudio';

/**
 * AudioPlayer Component for Serbian vocabulary pronunciation
 * Provides play button with visual feedback for TTS pronunciation
 */
const AudioPlayer = ({
    word,
    className = '',
    style = {},
    showText = true,
    size = 'medium',
    disabled = false,
    onPlay = null,
    onStop = null,
    onError = null
}) => {
    const { isPlaying, isReady, isEnabled, playPronunciation, stopAudio } = useAudio();

    const handlePlay = async () => {
        if (!word || !isReady || !isEnabled || disabled) return;

        try {
            if (onPlay) onPlay();

            await playPronunciation(word, {
                onend: () => {
                    if (onStop) onStop();
                },
                onerror: (error) => {
                    console.error('Audio playback error:', error);
                    if (onError) onError(error);
                }
            });
        } catch (error) {
            console.error('Error in audio player:', error);
            if (onError) onError(error);
        }
    };

    const handleStop = () => {
        stopAudio();
        if (onStop) onStop();
    };

    // Determine button size
    const getSizeStyles = () => {
        switch (size) {
            case 'small':
                return {
                    padding: '8px 12px',
                    fontSize: '14px',
                    minWidth: '90px'
                };
            case 'large':
                return {
                    padding: '16px 24px',
                    fontSize: '18px',
                    minWidth: '140px'
                };
            default: // medium
                return {
                    padding: '12px 16px',
                    fontSize: '16px',
                    minWidth: '110px'
                };
        }
    };

    // Base button styles
    const buttonStyles = {
        backgroundColor: isPlaying ? '#ffc107' : '#007bff',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        cursor: disabled || !isReady || !isEnabled ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        transition: 'all 0.3s ease',
        opacity: disabled || !isReady || !isEnabled ? 0.6 : 1,
        ...getSizeStyles(),
        ...style
    };

    // Hover effect (only if not disabled)
    const handleMouseEnter = (e) => {
        if (!disabled && isReady && isEnabled) {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        }
    };

    const handleMouseLeave = (e) => {
        if (!disabled && isReady && isEnabled) {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = 'none';
        }
    };

    // Determine button content
    const getButtonContent = () => {
        if (!isReady) {
            return (
                <>
                    <span>⏳</span>
                    {showText && <span>Loading...</span>}
                </>
            );
        }

        if (!isEnabled) {
            return (
                <>
                    <span>🔇</span>
                    {showText && <span>Audio Off</span>}
                </>
            );
        }

        if (isPlaying) {
            return (
                <>
                    <span>🔊</span>
                    {showText && <span>Playing...</span>}
                </>
            );
        }

        return (
            <>
                <span>🔊</span>
                {showText && <span>Play</span>}
            </>
        );
    };

    return (
        <button
            className={`audio-player-btn ${className}`}
            style={buttonStyles}
            onClick={isPlaying ? handleStop : handlePlay}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            disabled={disabled || !isReady}
            title={
                !isReady
                    ? 'Loading audio...'
                    : !isEnabled
                        ? 'Audio is disabled'
                        : isPlaying
                            ? `Stop pronunciation of "${word}"`
                            : `Play pronunciation of "${word}"`
            }
        >
            {getButtonContent()}
        </button>
    );
};

export default AudioPlayer;
