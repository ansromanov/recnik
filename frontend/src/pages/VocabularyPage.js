import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

function VocabularyPage() {
    const [words, setWords] = useState([]);
    const [filteredWords, setFilteredWords] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchCategories();
        fetchWords();
    }, []);

    useEffect(() => {
        filterWords();
    }, [words, selectedCategory, searchTerm]);

    const fetchCategories = async () => {
        try {
            const response = await apiService.getCategories();
            setCategories(response.data);
        } catch (err) {
            console.error('Error fetching categories:', err);
        }
    };

    const fetchWords = async () => {
        try {
            setLoading(true);
            const response = await apiService.getWords();
            setWords(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load vocabulary');
            console.error('Error fetching words:', err);
        } finally {
            setLoading(false);
        }
    };

    const filterWords = () => {
        let filtered = words;

        if (selectedCategory) {
            filtered = filtered.filter(word => word.category_id === selectedCategory);
        }

        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(word =>
                word.serbian_word.toLowerCase().includes(term) ||
                word.english_translation.toLowerCase().includes(term)
            );
        }

        setFilteredWords(filtered);
    };

    const getMasteryColor = (level) => {
        if (level >= 80) return '#4CAF50';
        if (level >= 60) return '#8BC34A';
        if (level >= 40) return '#FFC107';
        if (level >= 20) return '#FF9800';
        return '#F44336';
    };

    if (loading) return <div className="loading">Loading vocabulary...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="container">
            <h1>My Vocabulary</h1>

            <div className="card">
                <div style={{ marginBottom: '20px' }}>
                    <input
                        type="text"
                        className="input-field"
                        placeholder="Search words..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="category-filter">
                    <div
                        className={`category-badge ${!selectedCategory ? 'active' : ''}`}
                        onClick={() => setSelectedCategory(null)}
                    >
                        All ({words.length})
                    </div>
                    {categories.map(cat => {
                        const count = words.filter(w => w.category_id === cat.id).length;
                        return (
                            <div
                                key={cat.id}
                                className={`category-badge ${selectedCategory === cat.id ? 'active' : ''}`}
                                onClick={() => setSelectedCategory(cat.id)}
                            >
                                {cat.name} ({count})
                            </div>
                        );
                    })}
                </div>
            </div>

            {filteredWords.length === 0 ? (
                <div className="card">
                    <p>No words found. Start by processing some Serbian text!</p>
                </div>
            ) : (
                <div className="word-grid">
                    {filteredWords.map(word => (
                        <div key={word.id} className="word-card">
                            <h3 style={{ marginBottom: '10px' }}>{word.serbian_word}</h3>
                            <p style={{ fontSize: '18px', marginBottom: '15px' }}>
                                {word.english_translation}
                            </p>

                            <div style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                                <span className="category-badge" style={{ backgroundColor: '#e0e0e0' }}>
                                    {word.category_name}
                                </span>
                            </div>

                            {word.mastery_level !== null && (
                                <div style={{ marginTop: '15px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                        <span style={{ fontSize: '12px', color: '#666' }}>Mastery</span>
                                        <span style={{ fontSize: '12px', color: '#666' }}>{word.mastery_level}%</span>
                                    </div>
                                    <div className="mastery-indicator">
                                        <div
                                            className="mastery-fill"
                                            style={{
                                                width: `${word.mastery_level}%`,
                                                backgroundColor: getMasteryColor(word.mastery_level)
                                            }}
                                        />
                                    </div>
                                    {word.times_practiced > 0 && (
                                        <p style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                                            Practiced {word.times_practiced} times
                                        </p>
                                    )}
                                </div>
                            )}

                            {word.context && (
                                <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                                    <p style={{ fontSize: '12px', color: '#666' }}>Context:</p>
                                    <p style={{ fontSize: '14px' }}>{word.context}</p>
                                </div>
                            )}

                            {word.notes && (
                                <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                                    <p style={{ fontSize: '12px', color: '#666' }}>Notes:</p>
                                    <p style={{ fontSize: '14px' }}>{word.notes}</p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            <div className="card" style={{ marginTop: '30px' }}>
                <h3>Vocabulary Statistics</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginTop: '20px' }}>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Total Words</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{words.length}</p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Mastered (80%+)</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => w.mastery_level >= 80).length}
                        </p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>In Progress</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => w.mastery_level > 0 && w.mastery_level < 80).length}
                        </p>
                    </div>
                    <div>
                        <p style={{ color: '#666', marginBottom: '5px' }}>Not Started</p>
                        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>
                            {words.filter(w => !w.mastery_level || w.mastery_level === 0).length}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default VocabularyPage;
