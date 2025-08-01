import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import { Link } from 'react-router-dom';
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

    // State for letter clicking game
    const [userWord, setUserWord] = useState('');
    const [availableLetters, setAvailableLetters] = useState([]);
    const [usedLetterIndices, setUsedLetterIndices] = useState([]);

    useEffect(() => {
        loadUserSettings();
        // Don't auto-start session on initial load, show game selection instead
        setLoading(false);
    }, []);

    // Load user settings
    const loadUserSettings = async () => {
        try {
            const response = await apiService.getSettings();
            if (response.data.settings) {
                setUserSettings(response.data.settings);
            }
        } catch (error) {
            console.error('Failed to load user settings:', error);
        }
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

                    if (imageResponse.data && imageResponse.data.image_data) {
                        setWordImage({
                            data: imageResponse.data.image_data,
                            photographer: imageResponse.data.photographer,
                            unsplash_id: imageResponse.data.unsplash_id
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
            const wordsResponse = await apiService.getPracticeWords(10, null, selectedGameMode);
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

        // If correct, fetch example sentence
        if (correct) {
            setLoadingSentence(true);
            try {
                const sentenceResponse = await apiService.getExampleSentence(
                    currentWord.serbian_word,
                    currentWord.english_translation,
                    currentWord.category_name
                );
                setExampleSentence(sentenceResponse.data.sentence);
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

    const handleNextWord = () => {
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
    };

    const completeSession = async () => {
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
        if (showResult || usedLetterIndices.includes(letterIndex)) return;

        const letter = availableLetters[letterIndex];
        const newUserWord = userWord + letter;
        const newUsedIndices = [...usedLetterIndices, letterIndex];

        setUserWord(newUserWord);
        setUsedLetterIndices(newUsedIndices);

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

        setUserWord(newUserWord);
        setUsedLetterIndices(newUsedIndices);
    };

    // Clear word
    const handleClearWord = () => {
        if (showResult) return;
        setUserWord('');
        setUsedLetterIndices([]);
    };

    return (
        <div className="practice-page-container">
            {/* Background image */}
            {wordImage && (
                <div
                    className={`word-background-image ${imageLoading ? 'loading' : 'loaded'}`}
                    style={{
                        backgroundImage: `url(data:image/jpeg;base64,${wordImage.data})`
                    }}
                />
            )}

            {/* Image attribution */}
            {wordImage && wordImage.photographer && (
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

                    <div className="word-with-image">
                        <h2 style={{
                            fontSize: currentWord.game_mode === 'letters' ? '24px' : '32px',
                            letterSpacing: currentWord.game_mode === 'letters' ? '3px' : 'normal',
                            fontFamily: currentWord.game_mode === 'letters' ? 'monospace' : 'inherit'
                        }}>
                            {currentWord.question}
                        </h2>
                        {wordImage && gameMode === 'translation' && (
                            <img
                                src={`data:image/jpeg;base64,${wordImage.data}`}
                                alt={currentWord.serbian_word}
                                className="word-image-preview"
                            />
                        )}
                    </div>

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
                                    {Array.from({ length: currentWord.correct_answer.length }).map((_, index) => (
                                        <div
                                            key={index}
                                            className={`letter-slot ${index < userWord.length ? 'filled' : ''}`}
                                        >
                                            {userWord[index] || ''}
                                        </div>
                                    ))}
                                </div>
                                <div className="word-length-indicator">
                                    {userWord.length} / {currentWord.correct_answer.length}
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
                                    className="btn btn-warning"
                                    onClick={handleBackspace}
                                    disabled={showResult || userWord.length === 0}
                                >
                                    ⌫ Backspace
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleClearWord}
                                    disabled={showResult || userWord.length === 0}
                                >
                                    🗑️ Clear
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
                                    {option}
                                </button>
                            ))}
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
                                            backgroundColor: exampleSentence.includes('Configure OpenAI') ? '#fff3cd' : '#e8f5e9',
                                            borderRadius: '8px',
                                            fontSize: '16px',
                                            lineHeight: '1.6'
                                        }}>
                                            <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '10px', color: exampleSentence.includes('Configure OpenAI') ? '#856404' : '#2e7d32' }}>
                                                Example sentence:
                                            </p>
                                            <p style={{ margin: 0 }}>
                                                {exampleSentence.includes('Configure OpenAI') ? (
                                                    <span>
                                                        <Link to="/settings">Configure OpenAI API key in Settings</Link> to see example sentences
                                                    </span>
                                                ) : (
                                                    highlightWordInSentence(exampleSentence, currentWord.serbian_word)
                                                )}
                                            </p>
                                        </div>
                                    )}
                                    {loadingSentence && (
                                        <div style={{ marginTop: '20px', textAlign: 'center', color: '#666' }}>
                                            Loading example sentence...
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="error">
                                    ✗ Incorrect. The correct answer is: <strong>{currentWord.correct_answer}</strong>
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
                            onClick={() => {
                                if (window.confirm('Are you sure you want to end this session?')) {
                                    completeSession();
                                }
                            }}
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

                <div className="card">
                    <h3>Practice Tips:</h3>
                    <ul style={{ marginLeft: '20px', lineHeight: '1.8' }}>
                        <li>Click on the answer you think is correct</li>
                        <li>Correct answers will show an example sentence</li>
                        <li>The Serbian word is highlighted in green in the example</li>
                        <li>Words with lower mastery levels appear more frequently</li>
                        <li>Regular practice helps improve retention</li>
                        <li>Background images help with visual memory association</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}

export default PracticePage;
