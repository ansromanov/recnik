import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

function PracticePage() {
    const [practiceWords, setPracticeWords] = useState([]);
    const [currentWordIndex, setCurrentWordIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [sessionId, setSessionId] = useState(null);
    const [sessionStartTime, setSessionStartTime] = useState(null);
    const [showResult, setShowResult] = useState(false);
    const [isCorrect, setIsCorrect] = useState(false);
    const [sessionStats, setSessionStats] = useState({
        total: 0,
        correct: 0
    });
    const [sessionComplete, setSessionComplete] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        startNewSession();
    }, []);

    const startNewSession = async () => {
        try {
            setLoading(true);
            setError(null);

            // Start practice session
            const sessionResponse = await apiService.startPracticeSession();
            setSessionId(sessionResponse.data.id);
            setSessionStartTime(Date.now());

            // Get practice words
            const wordsResponse = await apiService.getPracticeWords(10);
            if (wordsResponse.data.length === 0) {
                setError('No words available for practice. Please add some words to your vocabulary first.');
                setLoading(false);
                return;
            }

            setPracticeWords(wordsResponse.data);
            setCurrentWordIndex(0);
            setSessionStats({ total: 0, correct: 0 });
            setSessionComplete(false);
            setShowResult(false);
            setUserAnswer('');
        } catch (err) {
            setError('Failed to start practice session');
            console.error('Error starting practice session:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitAnswer = async () => {
        if (!userAnswer.trim()) return;

        const currentWord = practiceWords[currentWordIndex];
        const correct = userAnswer.toLowerCase().trim() === currentWord.english_translation.toLowerCase().trim();

        setIsCorrect(correct);
        setShowResult(true);

        // Submit result to backend
        try {
            await apiService.submitPracticeResult(
                sessionId,
                currentWord.id,
                correct,
                Math.floor((Date.now() - sessionStartTime) / 1000)
            );

            setSessionStats(prev => ({
                total: prev.total + 1,
                correct: prev.correct + (correct ? 1 : 0)
            }));
        } catch (err) {
            console.error('Error submitting practice result:', err);
        }
    };

    const handleNextWord = () => {
        if (currentWordIndex < practiceWords.length - 1) {
            setCurrentWordIndex(prev => prev + 1);
            setUserAnswer('');
            setShowResult(false);
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

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            if (showResult) {
                handleNextWord();
            } else {
                handleSubmitAnswer();
            }
        }
    };

    if (loading) return <div className="loading">Loading practice session...</div>;
    if (error) return (
        <div className="container">
            <div className="error">{error}</div>
            <button className="btn" onClick={startNewSession}>Try Again</button>
        </div>
    );

    if (sessionComplete) {
        return (
            <div className="container">
                <div className="practice-card">
                    <h2>Session Complete!</h2>
                    <div style={{ marginTop: '30px', fontSize: '20px' }}>
                        <p>Total Questions: {sessionStats.total}</p>
                        <p>Correct Answers: {sessionStats.correct}</p>
                        <p>Accuracy: {sessionStats.accuracy}%</p>
                    </div>
                    <button
                        className="btn"
                        onClick={startNewSession}
                        style={{ marginTop: '30px' }}
                    >
                        Start New Session
                    </button>
                </div>
            </div>
        );
    }

    const currentWord = practiceWords[currentWordIndex];
    const progress = ((currentWordIndex + 1) / practiceWords.length) * 100;

    return (
        <div className="container">
            <h1>Practice Vocabulary</h1>

            <div className="practice-card">
                <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%` }} />
                </div>

                <p style={{ textAlign: 'right', color: '#666', marginBottom: '20px' }}>
                    Word {currentWordIndex + 1} of {practiceWords.length}
                </p>

                <h2>{currentWord.serbian_word}</h2>

                {currentWord.category_name && (
                    <span className="category-badge" style={{ backgroundColor: '#e0e0e0', marginTop: '10px' }}>
                        {currentWord.category_name}
                    </span>
                )}

                <input
                    type="text"
                    className="practice-input"
                    placeholder="Enter English translation..."
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={showResult}
                    autoFocus
                />

                {showResult && (
                    <div style={{ marginTop: '20px' }}>
                        {isCorrect ? (
                            <div className="success">
                                ✓ Correct!
                            </div>
                        ) : (
                            <div className="error">
                                ✗ Incorrect. The correct answer is: <strong>{currentWord.english_translation}</strong>
                            </div>
                        )}
                    </div>
                )}

                <div className="button-group">
                    {!showResult ? (
                        <button
                            className="btn"
                            onClick={handleSubmitAnswer}
                            disabled={!userAnswer.trim()}
                        >
                            Submit Answer
                        </button>
                    ) : (
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
                    <li>Take your time to think about the translation</li>
                    <li>Press Enter to submit your answer or continue to the next word</li>
                    <li>Words with lower mastery levels appear more frequently</li>
                    <li>Regular practice helps improve retention</li>
                </ul>
            </div>
        </div>
    );
}

export default PracticePage;
