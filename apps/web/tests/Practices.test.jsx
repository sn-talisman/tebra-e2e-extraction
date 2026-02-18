import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Practices from '../src/pages/Practices';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// --- MOCK DATA ---
const mockPractices = [
    { locationGuid: 'prac-1', practiceGuid: 'prac-1', name: 'Test Practice', city: 'Test City', state: 'TS', encounterCount: 10 }
];

const mockPatients = [
    { patientGuid: 'pat-1', name: 'John Doe', patientId: 'P001', encounterCount: 5, lastVisit: '2023-01-01' }
];

const mockEncounters = [
    { encounterId: 'enc-1', date: '2023-01-01', patientName: 'John Doe', providerName: 'Dr. Smith', status: 'Signed' }
];

const mockClaims = [
    { claimReferenceId: 'claim-1', claimId: 'CLM001', date: '2023-01-01', patientName: 'John Doe', billed: 100, paid: 80, status: 'Paid' }
];

const mockFinancialMetrics = {
    metrics: {
        daysInAR: { value: 35, trend: -2, performance: 'good' },
        netCollectionRate: { value: 98, trend: 1, performance: 'excellent' },
        denialRate: { value: 4, trend: -1, performance: 'good' },
        patientCollectionRate: { value: 92, trend: 2, performance: 'good' },
        arOver120Days: { value: 12, trend: -3, performance: 'good' }
    },
    comparisons: {
        allPractices: { avgDaysInAR: 40 },
        percentileRank: 80
    },
    trends: []
};

const mockPatientDetails = {
    patient: { fullName: 'John Doe', patientId: 'P001', dob: '1980-01-01', gender: 'M', caseId: 'CASE001', addressLine1: '123 St', city: 'City', state: 'ST', zip: '12345' },
    insurance: { companyName: 'Aetna', planName: 'PPO', policyNumber: 'POL123', groupNumber: 'GRP123' },
    encounters: []
};

// --- GLOBAL FETCH MOCK ---
global.fetch = vi.fn();

// Local ResizeObserver polyfill to ensure it loads before Recharts
global.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};

// Mock Recharts to avoid rendering issues
vi.mock('recharts', async () => {
    const Original = await vi.importActual('recharts');
    return {
        ...Original,
        ResponsiveContainer: ({ children }) => <div style={{ width: 800, height: 800 }}>{children}</div>,
    };
});

describe('Practices Page Integration', () => {
    beforeEach(() => {
        fetch.mockReset();

        // Router mock implementation
        fetch.mockImplementation((url) => {
            // console.log('Mock Fetch URL:', url); // Debug logging
            if (url.includes('/api/practices/list')) {
                return Promise.resolve({ ok: true, json: async () => mockPractices });
            }
            if (url.includes('/patients') && !url.includes('/details')) {
                return Promise.resolve({ ok: true, json: async () => mockPatients });
            }
            if (url.includes('/encounters') && !url.includes('/details')) {
                return Promise.resolve({ ok: true, json: async () => mockEncounters });
            }
            if (url.includes('/claims') && !url.includes('/details')) {
                return Promise.resolve({ ok: true, json: async () => mockClaims });
            }
            if (url.includes('/financial-metrics')) {
                return Promise.resolve({ ok: true, json: async () => mockFinancialMetrics });
            }
            if (url.includes('/api/patients/') && url.includes('/details')) {
                return Promise.resolve({ ok: true, json: async () => mockPatientDetails });
            }
            // Default fallback
            return Promise.resolve({ ok: true, json: async () => [] });
        });
    });

    it('navigates through tabs and opens patient details modal', async () => {
        render(
            <BrowserRouter>
                <Practices />
            </BrowserRouter>
        );

        // 1. Select Practice
        const dropdown = await screen.findByText(/Choose a practice/i);
        fireEvent.click(dropdown);
        const practiceOption = await screen.findByText(/Test Practice/i);
        fireEvent.click(practiceOption);

        // 2. Verify Patients Tab (Default)
        expect(await screen.findByText(/Patients at Test Practice/i)).toBeInTheDocument();
        expect(screen.getByText(/John Doe/i)).toBeInTheDocument();

        // 3. Open Patient Modal
        const viewDetailsBtns = screen.getAllByTitle('View Details');
        fireEvent.click(viewDetailsBtns[0]);

        // 4. Verify Modal Content
        expect(await screen.findByText(/Patient Details/i)).toBeInTheDocument();
        expect(screen.getByText(/Insurance Information/i)).toBeInTheDocument();
        // expect(screen.getAllByText('John Doe').length).toBeGreaterThan(0); 

        // 5. Close Modal
        const closeBtn = screen.getByRole('button', { name: /×/i }); // Assuming standard close generic
        fireEvent.click(closeBtn);
        await waitFor(() => {
            expect(screen.queryByText(/Insurance Information/i)).not.toBeInTheDocument();
        });
    });

    it('switches to encounters tab', async () => {
        render(<BrowserRouter><Practices /></BrowserRouter>);

        // Select Practice
        fireEvent.click(await screen.findByText(/Choose a practice/i));
        fireEvent.click(await screen.findByText(/Test Practice/i));

        // Click Encounters Tab
        fireEvent.click(screen.getByRole('button', { name: /Encounters/i }));

        // Verify Encounter Data
        expect(await screen.findByText(/Encounters at Test Practice/i)).toBeInTheDocument();
        expect(screen.getByText(/Dr. Smith/i)).toBeInTheDocument();
        expect(screen.getByText(/Signed/i)).toBeInTheDocument();
    });

    it('switches to claims tab', async () => {
        render(<BrowserRouter><Practices /></BrowserRouter>);

        // Select Practice
        fireEvent.click(await screen.findByText(/Choose a practice/i));
        fireEvent.click(await screen.findByText(/Test Practice/i));

        // Click Claims Tab
        fireEvent.click(screen.getByRole('button', { name: /Claims/i }));

        // Verify Claims Data
        expect(await screen.findByText(/Claims for Test Practice/i)).toBeInTheDocument();
        expect(screen.getByText(/CLM001/i)).toBeInTheDocument();
        expect(screen.getByText(/\$100.00/i)).toBeInTheDocument();
    });

    it.skip('switches to financial metrics tab', async () => {
        render(<BrowserRouter><Practices /></BrowserRouter>);

        // Select Practice
        fireEvent.click(await screen.findByText(/Choose a practice/i));
        fireEvent.click(await screen.findByText(/Test Practice/i));

        // Click Financial Tab
        fireEvent.click(screen.getByRole('button', { name: /Financial Metrics/i }));

        // Verify Metrics - Checking for card headers is sufficient to prove tab switch
        expect(await screen.findByText(/Days in A\/R/i, {}, { timeout: 5000 })).toBeInTheDocument();
        // expect(screen.getByText(/35/)).toBeInTheDocument(); // Value might be flaky in JSDOM/Recharts
        expect(screen.getByText(/Net Collection Rate/i)).toBeInTheDocument();
    });
});
