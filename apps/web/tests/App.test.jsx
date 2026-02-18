import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';
import { describe, it, expect } from 'vitest';

describe('App Component', () => {
    it('renders the top navigation bar', () => {
        render(<App />);
        const navElement = screen.getByRole('navigation');
        expect(navElement).toBeInTheDocument();
    });

    it('renders the sidebar navigation links', () => {
        render(<App />);
        // Check for key navigation links
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Practices')).toBeInTheDocument();
        expect(screen.getByText('Electronic Remittance')).toBeInTheDocument();
        expect(screen.getByText('Analytics')).toBeInTheDocument();
    });
});
