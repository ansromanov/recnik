import React, { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';
import soundService from '../services/soundService';
import { Link } from 'react-router-dom';
import CustomModal from '../components/CustomModal';
import { useAutoPlayVoice } from '../hooks/useAutoPlayVoice';
import './PracticePage.css';

function PracticePage() {
    const [practiceWords, setPracticeWords] = useState([]);
    const [currentWordIndex, setCurrentWordIndex] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState('');
    const [sessionId, setSessionId] = useState(null);
    const [sessionStartTime, setSessionStartTime] = useState(null);
    const [questionStartTime, setQuestionStartTime] = useState(null);
    const [showResult, setShowResult] = useState(false);
    const [isCorrect, setIsCorrect] = useState(false);
    const [exampleSentence, setExampleSentence] = useState('');
    const [loadingSentence, setLoadingSentence] = useState(false);
    const [sessionStats, setSessionStats] = useState({
        total: 0,
        correct: 0
    });
    const [sessionComplete, setSessionComplete] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [wordImage, setWordImage] = useState(null);
    const [imageLoading, setImageLoading] = useState(false);
    const [userSettings, setUserSettings] = useState(null);
    const [autoAdvanceTimer, setAutoAdvanceTimer] = useState(null);
    const [gameMode, setGameMode] = useState('translation');
    const [showGameSelection, setShowGameSelection] = useState(true);
    const [showEndSessionModal, setShowEndSessionModal] = useState(false);

    // State for letter clicking game
    const [userWord, setUserWord] = useState('');
    const [availableLetters, setAvailableLetters] = useState([]);
    const [usedLetterIndices, setUsedLetterIndices] = useState([]);
    const [letterStates, setLetterStates] = useState([]); // Track correct/incorrect letter positions
    const [mistakeCount, setMistakeCount] = useState(0);
    const [maxMistakes] = useState(3);

    // Auto-play voice hook
    const { autoPlayWord, isAutoPlayEnabled } = useAutoPlayVoice();

    // Debug states for audio
    const [audioDebugInfo, setAudioDebugInfo] = useState('');
    const [ttsStatus, setTtsStatus] = useState({});

    // Manual play function with debugging
    const handleManualPlay = async (word) => {
        console.log('🔊 Manual play triggered for word:', word);
        console.log('🔊 Auto-play enabled:', isAutoPlayEnabled());
        console.log('🔊 Current word data:', currentWord);

        setAudioDebugInfo(`Playing: ${word}`);

        try {
            // Get the actual word to play based on game mode
            const wordToPlay = currentWord.game_mode === 'audio'
                ? (currentWord.serbian_word || currentWord.audio_word || word)
                : word;

            console.log('🔊 Word to play:', wordToPlay);
            await autoPlayWord(wordToPlay);
            setAudioDebugInfo(`Successfully played: ${wordToPlay}`);
        } catch (error) {
            console.error('🔊 Manual play error:', error);
            setAudioDebugInfo(`Error playing: ${word} - ${error.message}`);
        }
    };

    // Update TTS status periodically for debugging
    useEffect(() => {
        const updateTTSStatus = () => {
            if (typeof window !== 'undefined' && window.responsiveVoice) {
                setTtsStatus({
                    responsiveVoiceLoaded: typeof window.responsiveVoice !== 'undefined',
                    voiceSupport: window.responsiveVoice.voiceSupport ? window.responsiveVoice.voiceSupport() : false,
                    isAutoPlayEnabled: isAutoPlayEnabled(),
                    currentVoice: window.responsiveVoice.getVoices ? window.responsiveVoice.getVoices().length : 0
                });
            }
        };

        updateTTSStatus();
        const interval = setInterval(updateTTSStatus, 2000);
        return () => clearInterval(interval);
    }, [isAutoPlayEnabled]);

    // Auto-play pronunciation when a new Serbian word is displayed
    useEffect(() => {
        if (practiceWords.length > 0 && currentWordIndex < practiceWords.length) {
            const currentWord = practiceWords[currentWordIndex];

            // Auto-play for Serbian words in translation and letters modes
            if (currentWord && currentWord.serbian_word &&
                (currentWord.game_mode === 'translation' || currentWord.game_mode === 'letters')) {
                autoPlayWord(currentWord.serbian_word);
            }

            // Auto-play for audio mode - play the hidden Serbian word immediately
            if (currentWord && currentWord.game_mode === 'audio') {
                // Try different possible field names for the Serbian word
                const audioWord = currentWord.serbian_word || currentWord.audio_word || currentWord.question;
                console.log('🔊 Audio mode - word to play:', audioWord, 'from currentWord:', currentWord);

                if (audioWord) {
                    // Delay slightly to let the interface load, then auto-play the audio
                    setTimeout(() => {
                        console.log('🔊 Auto-playing audio word:', audioWord);
                        autoPlayWord(audioWord);
                    }, 500);
                }
            }
        }
    }, [practiceWords, currentWordIndex, autoPlayWord]);

    // Load user settings
    const loadUserSettings = async () => {
        try {
            const response = await apiService.getSettings();
            if (response.data.settings) {
                setUserSettings(response.data.settings);
                // Update sound service based on user settings
                const soundsEnabled = response.data.settings.sounds_enabled !== undefined ?
                    response.data.settings.sounds_enabled : true;
                soundService.setEnabled(soundsEnabled);
            }
        } catch (error) {
            console.error('Failed to load user settings:', error);
        }
    };

    const completeSession = useCallback(async () => {
        try {
            const duration = Math.floor((Date.now() - sessionStartTime) / 1000);
            const response = await apiService.completePracticeSession(sessionId, duration);

            setSessionStats({
                total: response.data.total_questions,
                correct: response.data.correct_answers,
                accuracy: response.data.accuracy
            });
            setSessionComplete(true);
        } catch (err) {
            console.error('Error completing session:', err);
        }
    }, [sessionStartTime, sessionId]);

    const handleNextWord = useCallback(() => {
        // Clear auto-advance timer if it exists
        if (autoAdvanceTimer) {
            clearTimeout(autoAdvanceTimer);
            setAutoAdvanceTimer(null);
        }

        if (currentWordIndex < practiceWords.length - 1) {
            setCurrentWordIndex(prev => prev + 1);
            setSelectedAnswer('');
            setShowResult(false);
            setExampleSentence('');
            setQuestionStartTime(Date.now());
        } else {
            completeSession();
        }
    }, [autoAdvanceTimer, currentWordIndex, practiceWords.length, completeSession]);

    useEffect(() => {
        loadUserSettings();
        // Initialize sound service on first user interaction
        soundService.initializeOnUserInteraction();
        // Don't auto-start session on initial load, show game selection instead
        setLoading(false);
    }, []);

    // Keyboard shortcuts for translation and reverse translation games
    useEffect(() => {
        const handleKeyPress = (event) => {
            // Only handle keyboard shortcuts when we're in a game (not game selection, not completed, not loading)
            if (showGameSelection || sessionComplete || loading || error) return;

            // Only handle keyboard shortcuts for translation and reverse modes, not letters mode
            if (!practiceWords.length || currentWordIndex >= practiceWords.length) return;
            const currentWord = practiceWords[currentWordIndex];
            if (!currentWord || currentWord.game_mode === 'letters') return;

            // Don't handle shortcuts if modal is open
            if (showEndSessionModal) return;

            if (event.key === 'Escape') {
                event.preventDefault();
                setShowEndSessionModal(true);
            } else if (event.key === ' ' || event.key === 'Spacebar') {
                // Space key to go to next word (skip timeout)
                event.preventDefault();
                if (showResult) {
                    handleNextWord();
                }
            } else if (['1', '2', '3', '4'].includes(event.key)) {
                event.preventDefault();
                const optionIndex = parseInt(event.key) - 1;

                // Only proceed if we have options and the index is valid
                if (currentWord.options && optionIndex < currentWord.options.length && !showResult) {
                    handleAnswerSelect(currentWord.options[optionIndex]);
                }
            }
        };

        document.addEventListener('keydown', handleKeyPress);
        return () => {
            document.removeEventListener('keydown', handleKeyPress);
        };
    }, [showGameSelection, sessionComplete, loading, error, practiceWords, currentWordIndex, showResult, showEndSessionModal, handleNextWord]);

    const handleEndSession = () => {
        setShowEndSessionModal(false);
        completeSession();
    };

    const handleCancelEndSession = () => {
        setShowEndSessionModal(false);
    };

    // Fetch word image when current word changes
    useEffect(() => {
        const fetchWordImage = async () => {
            if (practiceWords.length > 0 && currentWordIndex < practiceWords.length) {
                const currentWord = practiceWords[currentWordIndex];
                setImageLoading(true);
                setWordImage(null);

                try {
                    const imageResponse = await apiService.searchImage(
                        currentWord.serbian_word,
                        currentWord.english_translation
                    );

                    if (imageResponse.data && imageResponse.data.success && imageResponse.data.image) {
                        setWordImage({
                            data: imageResponse.data.image.image_data,
                            photographer: imageResponse.data.image.photographer,
                            unsplash_id: imageResponse.data.image.unsplash_id
                        });
                    }
                } catch (err) {
                    console.log('No image available for current word');
                    setWordImage(null);
                } finally {
                    setImageLoading(false);
                }
            }
        };

        fetchWordImage();
    }, [practiceWords, currentWordIndex]);

    // Initialize letter game when word changes
    useEffect(() => {
        if (practiceWords.length > 0 && currentWordIndex < practiceWords.length) {
            const currentWord = practiceWords[currentWordIndex];
            if (currentWord && currentWord.game_mode === 'letters' && currentWord.letters) {
                setUserWord('');
                setAvailableLetters(currentWord.letters);
                setUsedLetterIndices([]);
                setLetterStates([]);
                setMistakeCount(0);
            }
        }
    }, [practiceWords, currentWordIndex]);

    const startNewSession = async (selectedGameMode = gameMode) => {
        try {
            setLoading(true);
            setError(null);

            // Start practice session
            const sessionResponse = await apiService.startPracticeSession();
            setSessionId(sessionResponse.data.id);
            setSessionStartTime(Date.now());

            // Get practice words with multiple choice options for selected game mode
            const roundCount = userSettings?.practice_round_count || 10;
            const wordsResponse = await apiService.getPracticeWords(roundCount, null, selectedGameMode);
            if (wordsResponse.data.length === 0) {
                setError('No words available for practice. Please add some words to your vocabulary first.');
                setLoading(false);
                return;
            }

            setPracticeWords(wordsResponse.data);
            setCurrentWordIndex(0);
            setQuestionStartTime(Date.now());
            setSessionStats({ total: 0, correct: 0 });
            setSessionComplete(false);
            setShowResult(false);
            setSelectedAnswer('');
            setExampleSentence('');
            setShowGameSelection(false);
        } catch (err) {
            setError('Failed to start practice session');
            console.error('Error starting practice session:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleGameModeSelect = (mode) => {
        setGameMode(mode);
        startNewSession(mode);
    };

    const getGameModeTitle = (mode) => {
        switch (mode) {
            case 'translation':
                return 'Serbian → English';
            case 'reverse':
                return 'English → Serbian';
            case 'letters':
                return 'Make Word from Letters';
            case 'audio':
                return 'Audio Guessing';
            default:
                return 'Translation Practice';
        }
    };

    const getQuestionPrompt = (word) => {
        switch (word.game_mode) {
            case 'translation':
                return 'Choose the correct English translation:';
            case 'reverse':
                return 'Choose the correct Serbian word:';
            case 'letters':
                return `Arrange the letters to form the Serbian word for "${word.hint}":`;
            default:
                return 'Choose the correct answer:';
        }
    };

    const handleAnswerSelect = async (answer) => {
        if (showResult) return;

        setSelectedAnswer(answer);
        const currentWord = practiceWords[currentWordIndex];
        const correct = answer === currentWord.correct_answer;
        const responseTime = Math.floor((Date.now() - questionStartTime) / 1000);

        setIsCorrect(correct);
        setShowResult(true);

        // Play sound effect
        if (correct) {
            soundService.playCorrect();

            // Auto-play pronunciation for reverse mode when answer is correct
            if (currentWord.game_mode === 'reverse' && currentWord.correct_answer) {
                // Delay the auto-play slightly to let the correct sound finish
                setTimeout(() => {
                    autoPlayWord(currentWord.correct_answer);
                }, 500);
            }
        } else {
            soundService.playIncorrect();
        }

        // If correct, fetch example sentence
        if (correct) {
            setLoadingSentence(true);
            try {
                const sentenceResponse = await apiService.getExampleSentence(
                    currentWord.serbian_word,
                    currentWord.english_translation,
                    currentWord.category_name
                );
                // Handle both new format (with english translation) and old format (serbian only)
                const sentenceData = sentenceResponse.data;
                let sentence;
                if (sentenceData.sentence && typeof sentenceData.sentence === 'object') {
                    // New format: {serbian: "...", english: "..."}
                    sentence = sentenceData.sentence;
                    setExampleSentence(sentence);
                } else if (typeof sentenceData.sentence === 'string') {
                    // Old format: just serbian text
                    sentence = { serbian: sentenceData.sentence, english: '' };
                    setExampleSentence(sentence);
                } else {
                    sentence = { serbian: '', english: '' };
                    setExampleSentence(sentence);
                }

                // Auto-play the Serbian example sentence
                if (sentence && sentence.serbian) {
                    // Delay the sentence pronunciation to let other audio finish
                    setTimeout(() => {
                        autoPlayWord(sentence.serbian, 1000); // 1 second delay for sentence
                    }, 1500);
                }
            } catch (err) {
                console.error('Error fetching example sentence:', err);
                if (err.response && err.response.status === 400) {
                    setExampleSentence('Configure OpenAI API key in Settings to see example sentences');
                } else {
                    setExampleSentence('');
                }
            } finally {
                setLoadingSentence(false);
            }
        }

        // Submit result to backend
        try {
            await apiService.submitPracticeResult(
                sessionId,
                currentWord.id,
                correct,
                responseTime
            );

            setSessionStats(prev => ({
                total: prev.total + 1,
                correct: prev.correct + (correct ? 1 : 0)
            }));
        } catch (err) {
            console.error('Error submitting practice result:', err);
        }

        // Start auto-advance timer if enabled
        if (userSettings && userSettings.auto_advance_enabled) {
            const timeout = (userSettings.auto_advance_timeout || 3) * 1000; // Convert to milliseconds
            const timer = setTimeout(() => {
                handleNextWord();
            }, timeout);
            setAutoAdvanceTimer(timer);
        }
    };

    const highlightWordInSentence = (sentence, word) => {
        if (!sentence || !word) return sentence;

        // Create a regex that matches the word (case-insensitive)
        const regex = new RegExp(`\\b${word}\\b`, 'gi');
        const parts = sentence.split(regex);
        const matches = sentence.match(regex) || [];

        return (
            <>
                {parts.map((part, index) => (
                    <React.Fragment key={index}>
                        {part}
                        {index < matches.length && (
                            <span style={{ color: '#4CAF50', fontWeight: 'bold' }}>
                                {matches[index]}
                            </span>
                        )}
                    </React.Fragment>
                ))}
            </>
        );
    };

    if (loading) return (
        <div className="practice-page-container">
            <div className="loading">Loading practice session...</div>
        </div>
    );

    if (error) return (
        <div className="practice-page-container">
            <div className="container">
                <div className="error">{error}</div>
                <button className="btn" onClick={startNewSession}>Try Again</button>
            </div>
        </div>
    );

    if (sessionComplete) {
        return (
            <div className="practice-page-container">
                <div className="container">
                    <div className="practice-card">
                        <h2>Session Complete!</h2>
                        <div style={{ marginTop: '20px', marginBottom: '20px' }}>
                            <h4>Game Mode: {getGameModeTitle(gameMode)}</h4>
                        </div>
                        <div style={{ marginTop: '30px', fontSize: '20px' }}>
                            <p>Total Questions: {sessionStats.total}</p>
                            <p>Correct Answers: {sessionStats.correct}</p>
                            <p>Accuracy: {sessionStats.accuracy}%</p>
                        </div>
                        <div style={{ marginTop: '30px', display: 'flex', gap: '15px', flexWrap: 'wrap', justifyContent: 'center' }}>
                            <button
                                className="btn"
                                onClick={() => {
                                    setShowGameSelection(true);
                                    setSessionComplete(false);
                                    setLoading(false);
                                }}
                            >
                                Choose New Game
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={() => startNewSession(gameMode)}
                            >
                                Same Game Again
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (showGameSelection) {
        return (
            <div className="practice-page-container">
                <div className="container">
                    <div className="practice-card">
                        <h2>Choose Your Practice Game</h2>
                        <p style={{ fontSize: '18px', color: '#666', marginBottom: '40px', textAlign: 'center' }}>
                            Select the type of practice you'd like to do:
                        </p>

                        <div style={{ display: 'grid', gap: '20px', maxWidth: '600px', margin: '0 auto' }}>
                            <div
                                className="game-mode-card"
                                onClick={() => handleGameModeSelect('translation')}
                                style={{
                                    padding: '25px',
                                    border: '2px solid #e0e0e0',
                                    borderRadius: '12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    backgroundColor: '#fff'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.borderColor = '#007bff';
                                    e.target.style.backgroundColor = '#f8f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.borderColor = '#e0e0e0';
                                    e.target.style.backgroundColor = '#fff';
                                }}
                            >
                                <h3 style={{ margin: '0 0 10px 0', color: '#007bff' }}>🇷🇸 → 🇺🇸 Translation</h3>
                                <p style={{ margin: '0', color: '#666' }}>
                                    See a Serbian word and choose the correct English translation
                                </p>
                                <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: '#999' }}>
                                    Example: "куća" → "house"
                                </p>
                            </div>

                            <div
                                className="game-mode-card"
                                onClick={() => handleGameModeSelect('reverse')}
                                style={{
                                    padding: '25px',
                                    border: '2px solid #e0e0e0',
                                    borderRadius: '12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    backgroundColor: '#fff'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.borderColor = '#28a745';
                                    e.target.style.backgroundColor = '#f8f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.borderColor = '#e0e0e0';
                                    e.target.style.backgroundColor = '#fff';
                                }}
                            >
                                <h3 style={{ margin: '0 0 10px 0', color: '#28a745' }}>🇺🇸 → 🇷🇸 Reverse Translation</h3>
                                <p style={{ margin: '0', color: '#666' }}>
                                    See an English word and choose the correct Serbian translation
                                </p>
                                <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: '#999' }}>
                                    Example: "house" → "kuća"
                                </p>
                            </div>

                            <div
                                className="game-mode-card"
                                onClick={() => handleGameModeSelect('letters')}
                                style={{
                                    padding: '25px',
                                    border: '2px solid #e0e0e0',
                                    borderRadius: '12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    backgroundColor: '#fff'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.borderColor = '#ffc107';
                                    e.target.style.backgroundColor = '#f8f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.borderColor = '#e0e0e0';
                                    e.target.style.backgroundColor = '#fff';
                                }}
                            >
                                <h3 style={{ margin: '0 0 10px 0', color: '#ffc107' }}>🔤 Make Word from Letters</h3>
                                <p style={{ margin: '0', color: '#666' }}>
                                    See scrambled letters and form the correct Serbian word
                                </p>
                                <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: '#999' }}>
                                    Example: "ćaku" → "kuća" (house)
                                </p>
                            </div>

                            <div
                                className="game-mode-card"
                                onClick={() => handleGameModeSelect('audio')}
                                style={{
                                    padding: '25px',
                                    border: '2px solid #e0e0e0',
                                    borderRadius: '12px',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    backgroundColor: '#fff'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.borderColor = '#dc3545';
                                    e.target.style.backgroundColor = '#f8f9fa';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.borderColor = '#e0e0e0';
                                    e.target.style.backgroundColor = '#fff';
                                }}
                            >
                                <h3 style={{ margin: '0 0 10px 0', color: '#dc3545' }}>🔊 Audio Guessing</h3>
                                <p style={{ margin: '0', color: '#666' }}>
                                    Listen to Serbian audio and choose the correct English translation
                                </p>
                                <p style={{ margin: '10px 0 0 0', fontSize: '14px', color: '#999' }}>
                                    Word and picture revealed only after correct answer
                                </p>
                            </div>
                        </div>

                        <div style={{ marginTop: '40px', textAlign: 'center' }}>
                            <p style={{ fontSize: '16px', color: '#666' }}>
                                💡 Each game mode helps you learn vocabulary in different ways!
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const currentWord = practiceWords[currentWordIndex];
    const progress = ((currentWordIndex + 1) / practiceWords.length) * 100;

    // Handle letter clicking
    const handleLetterClick = (letterIndex) => {
        if (showResult || usedLetterIndices.includes(letterIndex) || mistakeCount >= maxMistakes) return;

        const letter = availableLetters[letterIndex];
        const newUserWord = userWord + letter;
        const newUsedIndices = [...usedLetterIndices, letterIndex];
        const currentPosition = userWord.length;
        const correctLetter = currentWord.correct_answer[currentPosition];

        // Check if the letter is correct for this position
        const isCorrect = letter.toLowerCase() === correctLetter.toLowerCase();
        const newLetterStates = [...letterStates];
        newLetterStates[currentPosition] = isCorrect ? 'correct' : 'incorrect';

        setUserWord(newUserWord);
        setUsedLetterIndices(newUsedIndices);
        setLetterStates(newLetterStates);

        // If incorrect, increment mistake counter
        if (!isCorrect) {
            const newMistakeCount = mistakeCount + 1;
            setMistakeCount(newMistakeCount);

            // Auto-advance to next word after 3 mistakes
            if (newMistakeCount >= maxMistakes) {
                setTimeout(() => {
                    handleAnswerSelect(newUserWord); // This will be marked as incorrect
                }, 1000); // Give user time to see the mistake
                return;
            }
        }

        // Auto-submit when word is complete
        if (newUserWord.length === currentWord.correct_answer.length) {
            setTimeout(() => {
                handleAnswerSelect(newUserWord);
            }, 300); // Small delay to show the completed word
        }
    };

    // Handle backspace/undo
    const handleBackspace = () => {
        if (showResult || userWord.length === 0) return;

        const newUserWord = userWord.slice(0, -1);
        const newUsedIndices = usedLetterIndices.slice(0, -1);
        const newLetterStates = letterStates.slice(0, -1);

        setUserWord(newUserWord);
        setUsedLetterIndices(newUsedIndices);
        setLetterStates(newLetterStates);
    };

    // Clear word
    const handleClearWord = () => {
        if (showResult) return;
        setUserWord('');
        setUsedLetterIndices([]);
        setLetterStates([]);
    };

    return (
        <div className="practice-page-container">
            {/* Background image - hidden in audio mode until correct answer */}
            {wordImage && (currentWord.game_mode !== 'audio' || showResult && isCorrect) && (
                <div
                    className={`word-background-image ${imageLoading ? 'loading' : 'loaded'}`}
                    style={{
                        backgroundImage: `url(data:image/jpeg;base64,${wordImage.data})`
                    }}
                />
            )}

            {/* Image attribution - hidden in audio mode until correct answer */}
            {wordImage && wordImage.photographer && (currentWord.game_mode !== 'audio' || showResult && isCorrect) && (
                <div className="image-attribution">
                    Photo by <a href={`https://unsplash.com/@${wordImage.unsplash_id}`} target="_blank" rel="noopener noreferrer">
                        {wordImage.photographer}
                    </a> on <a href="https://unsplash.com" target="_blank" rel="noopener noreferrer">Unsplash</a>
                </div>
            )}

            <div className="container">
                <h1>Practice Vocabulary</h1>
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                    <span style={{
                        backgroundColor: '#007bff',
                        color: 'white',
                        padding: '5px 15px',
                        borderRadius: '20px',
                        fontSize: '14px'
                    }}>
                        {getGameModeTitle(gameMode)}
                    </span>
                </div>

                <div className="practice-card">
                    <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${progress}%` }} />
                    </div>

                    <p style={{ textAlign: 'right', color: '#666', marginBottom: '20px' }}>
                        Word {currentWordIndex + 1} of {practiceWords.length}
                    </p>

                    {/* Audio mode special interface */}
                    {currentWord.game_mode === 'audio' ? (
                        <div className="audio-game-container" style={{ textAlign: 'center', marginBottom: '30px' }}>
                            {/* Enhanced Audio play section */}
                            <div style={{ marginBottom: '30px' }}>
                                <div style={{
                                    padding: '40px',
                                    backgroundColor: showResult && isCorrect ? '#e8f5e9' : '#f8f9fa',
                                    borderRadius: '20px',
                                    marginBottom: '20px',
                                    border: showResult && isCorrect ? '3px solid #4CAF50' : '3px dashed #007bff',
                                    transition: 'all 0.3s ease'
                                }}>
                                    <div style={{
                                        fontSize: '48px',
                                        marginBottom: '15px',
                                        animation: autoPlayWord ? 'pulse 1.5s infinite' : 'none'
                                    }}>
                                        {showResult && isCorrect ? '🎉' : '🔊'}
                                    </div>

                                    {/* Main play button with enhanced states */}
                                    <button
                                        className="btn"
                                        onClick={() => {
                                            const wordToPlay = showResult && isCorrect
                                                ? (currentWord.serbian_word || currentWord.hidden_word)
                                                : (currentWord.serbian_word || currentWord.audio_word || currentWord.question);
                                            console.log('🔊 Play button clicked, playing:', wordToPlay);
                                            handleManualPlay(wordToPlay);
                                        }}
                                        style={{
                                            fontSize: '18px',
                                            padding: '15px 30px',
                                            backgroundColor: showResult && isCorrect ? '#4CAF50' : '#007bff',
                                            border: 'none',
                                            borderRadius: '50px',
                                            boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                                            transition: 'all 0.3s ease',
                                            marginBottom: '10px'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.transform = 'translateY(-2px)';
                                            e.target.style.boxShadow = '0 6px 12px rgba(0,0,0,0.3)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.transform = 'translateY(0)';
                                            e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                                        }}
                                    >
                                        🔄 {showResult && isCorrect ? 'Play Again' : 'Play Audio Again'}
                                    </button>

                                    {/* Audio visualization bars */}
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'end',
                                        gap: '3px',
                                        height: '30px',
                                        marginBottom: '15px'
                                    }}>
                                        {[...Array(8)].map((_, i) => (
                                            <div
                                                key={i}
                                                style={{
                                                    width: '4px',
                                                    height: `${Math.random() * 20 + 10}px`,
                                                    backgroundColor: showResult && isCorrect ? '#4CAF50' : '#007bff',
                                                    borderRadius: '2px',
                                                    animation: 'audioWave 1.2s infinite ease-in-out',
                                                    animationDelay: `${i * 0.1}s`
                                                }}
                                            />
                                        ))}
                                    </div>

                                    <p style={{
                                        marginTop: '15px',
                                        color: showResult && isCorrect ? '#2e7d32' : '#666',
                                        fontSize: '16px',
                                        fontWeight: showResult && isCorrect ? 'bold' : 'normal'
                                    }}>
                                        {showResult && isCorrect
                                            ? '🎯 Perfect! You identified the word correctly!'
                                            : '🎧 Listen carefully and choose the correct English translation'
                                        }
                                    </p>

                                    {/* Playback counter */}
                                    <div style={{
                                        marginTop: '10px',
                                        fontSize: '14px',
                                        color: '#888'
                                    }}>
                                        💡 Tip: You can replay the audio as many times as you need
                                    </div>
                                </div>
                            </div>

                            {/* Enhanced revealed content after correct answer */}
                            {showResult && isCorrect && (
                                <div className="revealed-content" style={{
                                    padding: '25px',
                                    backgroundColor: '#e8f5e9',
                                    borderRadius: '15px',
                                    marginBottom: '20px',
                                    border: '3px solid #4CAF50',
                                    boxShadow: '0 8px 16px rgba(76, 175, 80, 0.2)',
                                    animation: 'slideInUp 0.5s ease-out'
                                }}>
                                    <div style={{
                                        textAlign: 'center',
                                        marginBottom: '20px'
                                    }}>
                                        <h3 style={{
                                            color: '#2e7d32',
                                            margin: '0 0 10px 0',
                                            fontSize: '22px'
                                        }}>
                                            🎉 Congratulations! The word was:
                                        </h3>
                                    </div>

                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '25px',
                                        justifyContent: 'center',
                                        flexWrap: 'wrap'
                                    }}>
                                        {wordImage && (
                                            <div style={{ textAlign: 'center' }}>
                                                <img
                                                    src={`data:image/jpeg;base64,${wordImage.data}`}
                                                    alt={currentWord.hidden_word}
                                                    style={{
                                                        width: '140px',
                                                        height: '140px',
                                                        objectFit: 'cover',
                                                        borderRadius: '15px',
                                                        boxShadow: '0 6px 12px rgba(0,0,0,0.15)',
                                                        border: '4px solid #4CAF50'
                                                    }}
                                                />
                                                <p style={{
                                                    fontSize: '12px',
                                                    color: '#888',
                                                    margin: '8px 0 0 0'
                                                }}>
                                                    Visual representation
                                                </p>
                                            </div>
                                        )}
                                        <div style={{ textAlign: 'center' }}>
                                            <h2 style={{
                                                fontSize: '32px',
                                                margin: '0 0 8px 0',
                                                color: '#2e7d32',
                                                fontWeight: 'bold'
                                            }}>
                                                {currentWord.hidden_word}
                                            </h2>
                                            <p style={{
                                                fontSize: '20px',
                                                color: '#555',
                                                margin: '0 0 15px 0',
                                                fontStyle: 'italic'
                                            }}>
                                                "{currentWord.hidden_translation}"
                                            </p>

                                            {/* Pronunciation button for revealed word */}
                                            <button
                                                className="btn btn-sm"
                                                onClick={() => {
                                                    const wordToPlay = currentWord.serbian_word || currentWord.hidden_word;
                                                    console.log('🔊 Pronounce again clicked:', wordToPlay);
                                                    handleManualPlay(wordToPlay);
                                                }}
                                                style={{
                                                    fontSize: '14px',
                                                    padding: '8px 16px',
                                                    backgroundColor: '#4CAF50',
                                                    border: 'none',
                                                    borderRadius: '20px',
                                                    color: 'white'
                                                }}
                                            >
                                                🔊 Pronounce Again
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Wrong answer feedback for audio mode */}
                            {showResult && !isCorrect && (
                                <div style={{
                                    padding: '20px',
                                    backgroundColor: '#ffebee',
                                    borderRadius: '12px',
                                    marginBottom: '20px',
                                    border: '2px solid #f44336',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '24px', marginBottom: '10px' }}>❌</div>
                                    <p style={{
                                        color: '#c62828',
                                        fontSize: '18px',
                                        margin: '0 0 15px 0',
                                        fontWeight: 'bold'
                                    }}>
                                        Not quite right! Try listening again.
                                    </p>
                                    <button
                                        className="btn"
                                        onClick={() => autoPlayWord(currentWord.audio_word)}
                                        style={{
                                            fontSize: '16px',
                                            padding: '10px 20px',
                                            backgroundColor: '#f44336',
                                            border: 'none',
                                            borderRadius: '25px',
                                            color: 'white'
                                        }}
                                    >
                                        🔊 Listen Again
                                    </button>
                                </div>
                            )}

                            {/* Debug information for audio issues */}
                            {process.env.NODE_ENV === 'development' && (
                                <div style={{
                                    marginTop: '20px',
                                    padding: '15px',
                                    backgroundColor: '#f8f9fa',
                                    borderRadius: '8px',
                                    fontSize: '12px',
                                    fontFamily: 'monospace',
                                    border: '1px solid #dee2e6'
                                }}>
                                    <h5 style={{ marginBottom: '10px', fontSize: '14px' }}>🔧 Debug Info:</h5>
                                    <div><strong>Audio Debug:</strong> {audioDebugInfo}</div>
                                    <div><strong>ResponsiveVoice:</strong> {ttsStatus.responsiveVoiceLoaded ? '✅ Loaded' : '❌ Not loaded'}</div>
                                    <div><strong>Voice Support:</strong> {ttsStatus.voiceSupport ? '✅ Supported' : '❌ Not supported'}</div>
                                    <div><strong>Auto-play Enabled:</strong> {ttsStatus.isAutoPlayEnabled ? '✅ Yes' : '❌ No'}</div>
                                    <div><strong>Available Voices:</strong> {ttsStatus.currentVoice || 0}</div>
                                    <div><strong>Current Word Data:</strong></div>
                                    <pre style={{ marginTop: '5px', fontSize: '10px', backgroundColor: '#e9ecef', padding: '8px', borderRadius: '4px' }}>
                                        {JSON.stringify({
                                            serbian_word: currentWord?.serbian_word,
                                            audio_word: currentWord?.audio_word,
                                            hidden_word: currentWord?.hidden_word,
                                            question: currentWord?.question,
                                            game_mode: currentWord?.game_mode
                                        }, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    ) : (
                        /* Regular word display for other modes */
                        <div className="word-with-image" style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '20px',
                            marginBottom: '20px',
                            flexWrap: 'wrap',
                            justifyContent: 'center'
                        }}>
                            {wordImage && (
                                <img
                                    src={`data:image/jpeg;base64,${wordImage.data}`}
                                    alt={currentWord.serbian_word}
                                    style={{
                                        width: '120px',
                                        height: '120px',
                                        objectFit: 'cover',
                                        borderRadius: '12px',
                                        boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
                                        border: '3px solid #fff'
                                    }}
                                />
                            )}
                            <div style={{ flex: '1', minWidth: '200px' }}>
                                <h2 style={{
                                    fontSize: currentWord.game_mode === 'letters' ? '24px' : '32px',
                                    letterSpacing: currentWord.game_mode === 'letters' ? '3px' : 'normal',
                                    fontFamily: currentWord.game_mode === 'letters' ? 'monospace' : 'inherit',
                                    margin: '0',
                                    textAlign: wordImage ? 'left' : 'center'
                                }}>
                                    {currentWord.question}
                                </h2>
                            </div>
                        </div>
                    )}

                    {currentWord.category_name && (
                        <span className="category-badge">
                            {currentWord.category_name}
                        </span>
                    )}

                    {currentWord.game_mode === 'letters' && currentWord.hint && (
                        <div style={{
                            textAlign: 'center',
                            margin: '15px 0',
                            padding: '10px',
                            backgroundColor: '#fff3cd',
                            borderRadius: '8px',
                            border: '1px solid #ffeaa7'
                        }}>
                            <span style={{ fontSize: '16px', color: '#856404' }}>
                                💡 Hint: {currentWord.hint}
                            </span>
                        </div>
                    )}

                    <p style={{ fontSize: '18px', color: '#666', marginTop: '20px', marginBottom: '30px' }}>
                        {getQuestionPrompt(currentWord)}
                    </p>

                    {/* Letter clicking interface for letters game mode */}
                    {currentWord.game_mode === 'letters' ? (
                        <div className="letters-game-container">
                            {/* User's current word display */}
                            <div className="user-word-display">
                                <div className="word-progress">
                                    {Array.from({ length: currentWord.correct_answer.length }).map((_, index) => {
                                        const letterState = letterStates[index];
                                        let slotClass = 'letter-slot';

                                        if (index < userWord.length) {
                                            slotClass += ' filled';
                                            if (letterState === 'correct') {
                                                slotClass += ' correct';
                                            } else if (letterState === 'incorrect') {
                                                slotClass += ' incorrect';
                                            }
                                        }

                                        return (
                                            <div key={index} className={slotClass}>
                                                {userWord[index] || ''}
                                            </div>
                                        );
                                    })}
                                </div>
                                <div className="word-length-indicator">
                                    {userWord.length} / {currentWord.correct_answer.length}
                                    {mistakeCount > 0 && (
                                        <span style={{ marginLeft: '10px', color: '#dc3545', fontSize: '12px' }}>
                                            Mistakes: {mistakeCount}/{maxMistakes}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Available letters to click */}
                            <div className="available-letters">
                                {availableLetters.map((letter, index) => (
                                    <button
                                        key={index}
                                        className={`letter-btn ${usedLetterIndices.includes(index) ? 'used' : ''}`}
                                        onClick={() => handleLetterClick(index)}
                                        disabled={showResult || usedLetterIndices.includes(index)}
                                    >
                                        {letter}
                                    </button>
                                ))}
                            </div>

                            {/* Action buttons */}
                            <div className="letter-game-actions">
                                <button
                                    className="btn"
                                    onClick={() => {
                                        const wordToPlay = currentWord.serbian_word || currentWord.audio_word || currentWord.question;
                                        console.log('🔊 Listen again clicked:', wordToPlay);
                                        handleManualPlay(wordToPlay);
                                    }}
                                    style={{
                                        fontSize: '16px',
                                        padding: '10px 20px',
                                        backgroundColor: '#f44336',
                                        border: 'none',
                                        borderRadius: '25px',
                                        color: 'white'
                                    }}
                                >
                                    🔊 Listen Again
                                </button>
                                {userWord.length === currentWord.correct_answer.length && !showResult && (
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => handleAnswerSelect(userWord)}
                                    >
                                        ✓ Submit
                                    </button>
                                )}
                            </div>
                        </div>
                    ) : (
                        /* Regular multiple choice interface for translation/reverse modes */
                        <div>
                            {/* Keyboard shortcuts hint */}
                            {!showResult && (
                                <div style={{
                                    textAlign: 'center',
                                    marginBottom: '15px',
                                    padding: '8px 15px',
                                    backgroundColor: '#e3f2fd',
                                    borderRadius: '20px',
                                    fontSize: '14px',
                                    color: '#1976d2',
                                    display: 'inline-block',
                                    width: '100%'
                                }}>
                                    💡 Use keyboard shortcuts: Press 1-{currentWord.options ? currentWord.options.length : 4} to select answers, Esc to end session
                                </div>
                            )}
                            {/* Space key hint when result is shown */}
                            {showResult && (
                                <div style={{
                                    textAlign: 'center',
                                    marginBottom: '15px',
                                    padding: '8px 15px',
                                    backgroundColor: '#e8f5e9',
                                    borderRadius: '20px',
                                    fontSize: '14px',
                                    color: '#2e7d32',
                                    display: 'inline-block',
                                    width: '100%'
                                }}>
                                    ⚡ Press Space to go to next word (skip timeout)
                                </div>
                            )}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '30px' }}>
                                {currentWord.options && currentWord.options.map((option, index) => (
                                    <button
                                        key={index}
                                        className={`btn ${showResult && option === currentWord.correct_answer
                                            ? 'btn-success'
                                            : showResult && option === selectedAnswer && !isCorrect
                                                ? 'btn-danger'
                                                : selectedAnswer === option && !showResult
                                                    ? 'btn-secondary'
                                                    : ''
                                            }`}
                                        onClick={() => handleAnswerSelect(option)}
                                        disabled={showResult}
                                        style={{
                                            padding: '15px 20px',
                                            fontSize: '16px',
                                            textAlign: 'center',
                                            position: 'relative',
                                            backgroundColor: showResult && option === currentWord.correct_answer
                                                ? '#4CAF50'
                                                : showResult && option === selectedAnswer && !isCorrect
                                                    ? '#f44336'
                                                    : selectedAnswer === option && !showResult
                                                        ? '#008CBA'
                                                        : '',
                                            color: (showResult && (option === currentWord.correct_answer || (option === selectedAnswer && !isCorrect))) || (selectedAnswer === option && !showResult)
                                                ? 'white'
                                                : ''
                                        }}
                                    >
                                        {/* Keyboard shortcut indicator */}
                                        {!showResult && (
                                            <span style={{
                                                position: 'absolute',
                                                top: '5px',
                                                left: '8px',
                                                fontSize: '12px',
                                                backgroundColor: 'rgba(0,0,0,0.1)',
                                                color: '#666',
                                                padding: '2px 6px',
                                                borderRadius: '3px',
                                                fontWeight: 'bold'
                                            }}>
                                                {index + 1}
                                            </span>
                                        )}
                                        {option}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {showResult && (
                        <div style={{ marginTop: '20px' }}>
                            {isCorrect ? (
                                <>
                                    <div className="success">
                                        ✓ Correct!
                                    </div>
                                    {exampleSentence && (
                                        <div style={{
                                            marginTop: '20px',
                                            padding: '15px',
                                            backgroundColor: (typeof exampleSentence === 'string' && exampleSentence.includes('Configure OpenAI')) ? '#fff3cd' : '#e8f5e9',
                                            borderRadius: '8px',
                                            fontSize: '16px',
                                            lineHeight: '1.6'
                                        }}>
                                            <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '10px', color: (typeof exampleSentence === 'string' && exampleSentence.includes('Configure OpenAI')) ? '#856404' : '#2e7d32' }}>
                                                Example sentence:
                                            </p>
                                            <div style={{ margin: 0 }}>
                                                {(typeof exampleSentence === 'string' && exampleSentence.includes('Configure OpenAI')) ? (
                                                    <span>
                                                        <Link to="/settings">Configure OpenAI API key in Settings</Link> to see example sentences
                                                    </span>
                                                ) : typeof exampleSentence === 'object' && exampleSentence.serbian ? (
                                                    <>
                                                        <p style={{ margin: '0 0 10px 0', fontSize: '16px' }}>
                                                            <strong>🇷🇸 Serbian:</strong> {highlightWordInSentence(exampleSentence.serbian || '', currentWord.serbian_word)}
                                                        </p>
                                                        {exampleSentence.english && (
                                                            <p style={{ margin: '0', fontSize: '16px', color: '#555' }}>
                                                                <strong>🇺🇸 English:</strong> {highlightWordInSentence(exampleSentence.english, currentWord.english_translation)}
                                                            </p>
                                                        )}
                                                    </>
                                                ) : typeof exampleSentence === 'string' ? (
                                                    <p style={{ margin: 0 }}>
                                                        {highlightWordInSentence(exampleSentence, currentWord.serbian_word)}
                                                    </p>
                                                ) : null}
                                            </div>
                                        </div>
                                    )}
                                    {loadingSentence && (
                                        <div style={{ marginTop: '20px', textAlign: 'center', color: '#666' }}>
                                            Loading example sentence...
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center', justifyContent: 'center' }}>
                                    <span style={{
                                        backgroundColor: '#dc3545',
                                        color: 'white',
                                        padding: '8px 15px',
                                        borderRadius: '6px',
                                        fontSize: '16px',
                                        fontWeight: 'bold'
                                    }}>
                                        {selectedAnswer}
                                    </span>
                                    <span style={{ fontSize: '18px', color: '#666' }}>→</span>
                                    <span style={{
                                        backgroundColor: '#ffc107',
                                        color: '#212529',
                                        padding: '8px 15px',
                                        borderRadius: '6px',
                                        fontSize: '16px',
                                        fontWeight: 'bold'
                                    }}>
                                        {currentWord.correct_answer}
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="button-group">
                        {showResult && (
                            <button
                                className="btn"
                                onClick={handleNextWord}
                            >
                                {currentWordIndex < practiceWords.length - 1 ? 'Next Word' : 'Finish Session'}
                            </button>
                        )}

                        <button
                            className="btn btn-secondary"
                            onClick={() => setShowEndSessionModal(true)}
                        >
                            End Session
                        </button>
                    </div>

                    <div style={{ marginTop: '30px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
                        <h4>Session Progress</h4>
                        <p>Correct: {sessionStats.correct} / {sessionStats.total}</p>
                        {sessionStats.total > 0 && (
                            <p>Current Accuracy: {Math.round((sessionStats.correct / sessionStats.total) * 100)}%</p>
                        )}
                    </div>
                </div>

            </div>

            {/* End Session Modal */}
            <CustomModal
                isOpen={showEndSessionModal}
                onClose={handleCancelEndSession}
                onConfirm={handleEndSession}
                title="End Practice Session"
                message="Are you sure you want to end this practice session? Your progress will be saved."
                type="confirm"
            />
        </div>
    );
}

export default PracticePage;
