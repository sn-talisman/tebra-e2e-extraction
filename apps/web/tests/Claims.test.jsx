import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Claims from '../src/pages/Claims';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock fetch globally
global.fetch = vi.fn();

describe('Claims Page', () => {
    beforeEach(() => {
        fetch.mockClear();
    });

    it('renders and fetches claims', async () => {
        const mockClaims = [
            { claimId: 'CLM001', patientName: 'John Doe', practiceName: 'Test Practice', date: '2023-01-01', billed: 100, paid: 80, status: 'Paid' }
        ];

        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockClaims,
        });

        render(
            <BrowserRouter>
                <Claims />
            </BrowserRouter>
        );

        // Check for title (might be immediate)
        expect(screen.getByText('Claims')).toBeInTheDocument();
        expect(screen.getByText('All Claims')).toBeInTheDocument();

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText('Claim ID')).toBeInTheDocument();
            expect(screen.getByText('CLM001')).toBeInTheDocument();
            expect(screen.getByText('John Doe')).toBeInTheDocument();
        });
    });

    it('shows no claims message when empty', async () => {
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        });

        render(
            <BrowserRouter>
                <Claims />
            </BrowserRouter>
        );

        await waitFor(() => {
            expect(screen.getByText('No claims found.')).toBeInTheDocument();
        });
    });
});
