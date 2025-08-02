import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token is invalid or expired
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const apiService = {
    // Health check
    healthCheck: () => api.get('/health'),

    // Categories
    getCategories: () => api.get('/categories'),

    // Words
    getWords: (categoryId) => {
        const params = categoryId ? { category_id: categoryId } : {};
        return api.get('/words', { params });
    },

    addWords: (words) => api.post('/words', { words }),

    processText: (text) => api.post('/process-text', { text }),

    // Practice
    getPracticeWords: (limit = 10, difficulty, mode = 'translation') => {
        const params = { limit, mode };
        if (difficulty) params.difficulty = difficulty;
        return api.get('/practice/words', { params });
    },

    startPracticeSession: () => api.post('/practice/start'),

    submitPracticeResult: (sessionId, wordId, wasCorrect, responseTime) =>
        api.post('/practice/submit', {
            session_id: sessionId,
            word_id: wordId,
            was_correct: wasCorrect,
            response_time_seconds: responseTime,
        }),

    completePracticeSession: (sessionId, durationSeconds) =>
        api.post('/practice/complete', {
            session_id: sessionId,
            duration_seconds: durationSeconds,
        }),

    getExampleSentence: (serbianWord, englishTranslation, category) =>
        api.post('/practice/example-sentence', {
            serbian_word: serbianWord,
            english_translation: englishTranslation,
            category: category,
        }),

    // Statistics
    getStats: () => api.get('/stats'),

    // Content (formerly News)
    getContent: (queryParams) => {
        const url = queryParams ? `/news?${queryParams}` : '/news';
        return api.get(url);
    },

    getContentSources: () => api.get('/news/sources'),

    // For backward compatibility
    getNewsSources: () => api.get('/news/sources'),

    // Content Generation
    generateDialogue: (topic, difficulty = 'intermediate', wordCount = 200) =>
        api.post('/content/dialogue', {
            topic,
            difficulty,
            word_count: wordCount
        }),

    generateSummary: (articleText, summaryType = 'brief') =>
        api.post('/content/summary', {
            article_text: articleText,
            type: summaryType
        }),

    generateVocabularyContent: (topic, targetWords = [], contentType = 'story') =>
        api.post('/content/vocabulary-context', {
            topic,
            target_words: targetWords,
            content_type: contentType
        }),

    getContentTypes: () => api.get('/content/types'),

    getRecentContent: (contentType = 'all', limit = 10) =>
        api.get('/content/recent', { params: { type: contentType, limit } }),

    // Settings
    getSettings: () => api.get('/settings'),
    updateSettings: (settings) => api.put('/settings', settings),

    // Top 100 Words
    getTop100WordsByCategory: (categoryId) => api.get(`/top100/categories/${categoryId}`),
    addTop100WordsToVocabulary: (wordIds) => api.post('/top100/add', { word_ids: wordIds }),

    // Image Service
    getWordImage: (wordId) => api.get(`/words/${wordId}/image`),
    searchImage: (serbianWord, englishTranslation) =>
        api.post('/images/search', {
            serbian_word: serbianWord,
            english_translation: englishTranslation
        }),
    clearImageCache: (serbianWord) =>
        api.post('/images/cache/clear', { serbian_word: serbianWord }),
    getImageCacheStats: () => api.get('/images/cache/stats'),

    // Word Search and Suggestions
    searchWords: (query) => api.get('/words/search', { params: { q: query } }),
    addSuggestedWord: (wordData) => api.post('/words/add-suggested', wordData),

    // Excluded Words
    getExcludedWords: () => api.get('/excluded-words'),
    excludeWordFromVocabulary: (wordId, reason = 'manual_removal') =>
        api.post(`/words/${wordId}/exclude`, { reason }),
    removeFromExcludedWords: (excludedWordId) => api.delete(`/excluded-words/${excludedWordId}`),
    bulkExcludeWords: (words, reason = 'news_parser_skip') =>
        api.post('/excluded-words/bulk', { words, reason }),

    // Streaks
    getUserStreaks: () => api.get('/streaks'),
    recordStreakActivity: (activityType, activityCount = 1) =>
        api.post('/streaks/activity', {
            activity_type: activityType,
            activity_count: activityCount
        }),
    getStreakLeaderboard: (streakType = 'daily', limit = 10) =>
        api.get('/streaks/leaderboard', { params: { type: streakType, limit } }),

    // XP System
    getUserXP: () => api.get('/xp'),
    awardXP: (activityType, xpAmount, activityDetails = {}) =>
        api.post('/xp/award', {
            activity_type: activityType,
            xp_amount: xpAmount,
            activity_details: activityDetails
        }),
    getXPLeaderboard: (limit = 10) =>
        api.get('/xp/leaderboard', { params: { limit } }),

    // Achievements
    getUserAchievements: () => api.get('/achievements'),
    checkAchievements: () => api.post('/achievements/check'),
};

// fetchWithAuth function for components that need it
export const fetchWithAuth = async (url, options = {}) => {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Token is invalid or expired
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    return response;
};

// Export individual functions for components that use them
export const processText = async (text) => {
    const response = await apiService.processText(text);
    return {
        words: response.data.translations.map((word, index) => ({
            id: index,
            serbian: word.serbian_word,
            english: word.english_translation,
            category: word.category_name,
            original: word.original_form
        }))
    };
};

export const fetchContent = async (queryParams) => {
    const response = await apiService.getContent(queryParams);
    return response.data;
};

// Keep fetchNews for backward compatibility
export const fetchNews = fetchContent;

export const generateExampleSentence = async (word) => {
    const response = await apiService.getExampleSentence(
        word.serbian_word,
        word.english_translation,
        word.category
    );
    return response.data;
};

export default apiService;
