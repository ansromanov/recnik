import React from 'react';
import { useAudio } from '../hooks/useAudio';

/**
 * VoiceSelector Component for choosing TTS voices
 * Allows users to select between different Serbian voice options
 */
const VoiceSelector = ({
    className = '',
    style = {},
    showLabel = true,
    size = 'medium',
    onVoiceChange = null
}) => {
    const { currentVoice, changeVoice, getAvailableVoices, isReady } = useAudio();
    const availableVoices = getAvailableVoices();

    const handleVoiceChange = (event) => {
        const selectedVoice = event.target.value;
        changeVoice(selectedVoice);
        if (onVoiceChange) {
            onVoiceChange(selectedVoice);
        }
    };

    // Determine size styles
    const getSizeStyles = () => {
        switch (size) {
            case 'small':
                return {
                    padding: '6px 10px',
                    fontSize: '14px',
                    minWidth: '140px'
                };
            case 'large':
                return {
                    padding: '14px 18px',
                    fontSize: '18px',
                    minWidth: '200px'
                };
            default: // medium
                return {
                    padding: '10px 14px',
                    fontSize: '16px',
                    minWidth: '170px'
                };
        }
    };

    const selectStyles = {
        backgroundColor: '#fff',
        border: '2px solid #007bff',
        borderRadius: '8px',
        color: '#333',
        cursor: isReady ? 'pointer' : 'not-allowed',
        opacity: isReady ? 1 : 0.6,
        transition: 'all 0.3s ease',
        ...getSizeStyles(),
        ...style
    };

    const labelStyles = {
        display: 'block',
        marginBottom: '8px',
        fontSize: size === 'small' ? '14px' : size === 'large' ? '18px' : '16px',
        fontWeight: '600',
        color: '#333'
    };

    const containerStyles = {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start'
    };

    return (
        <div className={`voice-selector ${className}`} style={containerStyles}>
            {showLabel && (
                <label htmlFor="voice-select" style={labelStyles}>
                    🎙️ Voice:
                </label>
            )}
            <select
                id="voice-select"
                value={currentVoice}
                onChange={handleVoiceChange}
                style={selectStyles}
                disabled={!isReady}
                title={isReady ? 'Select voice for pronunciation' : 'Loading voices...'}
            >
                {availableVoices.map(voice => (
                    <option key={voice.id} value={voice.id}>
                        {voice.name}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default VoiceSelector;
