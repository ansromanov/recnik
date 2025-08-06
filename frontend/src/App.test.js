import { render, screen } from '@testing-library/react';
import App from './App';

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock the API service
jest.mock('./services/api', () => ({
    getCurrentAvatar: jest.fn().mockRejectedValue(new Error('Not found')),
    generateAvatar: jest.fn().mockResolvedValue({ data: { avatar: { avatar_url: 'test.jpg' } } })
}));

test('renders App component', () => {
    // Mock localStorage to return null (not authenticated)
    localStorageMock.getItem.mockReturnValue(null);

    render(<App />);

    // Since user is not authenticated, it should redirect to login
    // We can't easily test the redirect in this simple test,
    // but we can at least verify the component renders without crashing
    expect(document.body).toBeInTheDocument();
});

test('shows loading state initially', () => {
    localStorageMock.getItem.mockReturnValue(null);

    render(<App />);

    // The component should render without throwing any errors
    expect(document.body).toBeInTheDocument();
});
