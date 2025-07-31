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
    getPracticeWords: (limit = 10, difficulty) => {
        const params = { limit };
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

    // News
    getNews: (queryParams) => {
        const url = queryParams ? `/news?${queryParams}` : '/news';
        return api.get(url);
    },

    getNewsSources: () => api.get('/news/sources'),

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

export const fetchNews = async (queryParams) => {
    const response = await apiService.getNews(queryParams);
    return response.data;
};

export const generateExampleSentence = async (word) => {
    const response = await apiService.getExampleSentence(
        word.serbian_word,
        word.english_translation,
        word.category
    );
    return response.data;
};

export default apiService;
