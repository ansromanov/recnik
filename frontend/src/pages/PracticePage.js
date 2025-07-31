import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

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

            // Get practice words with multiple choice options
            const wordsResponse = await apiService.getPracticeWords(10);
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
        } catch (err) {
            setError('Failed to start practice session');
            console.error('Error starting practice session:', err);
        } finally {
            setLoading(false);
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
                setExampleSentence('');
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
    };

    const handleNextWord = () => {
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

                <p style={{ fontSize: '18px', color: '#666', marginTop: '20px', marginBottom: '30px' }}>
                    Choose the correct English translation:
                </p>

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
                                        backgroundColor: '#e8f5e9',
                                        borderRadius: '8px',
                                        fontSize: '16px',
                                        lineHeight: '1.6'
                                    }}>
                                        <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '10px', color: '#2e7d32' }}>
                                            Example sentence:
                                        </p>
                                        <p style={{ margin: 0 }}>
                                            {highlightWordInSentence(exampleSentence, currentWord.serbian_word)}
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
                </ul>
            </div>
        </div>
    );
}

export default PracticePage;
