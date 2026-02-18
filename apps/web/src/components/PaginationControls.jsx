import React from 'react';

const PaginationControls = ({ currentPage, totalItems, itemsPerPage, onPageChange }) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    if (totalPages <= 1) return null;

    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', marginTop: '16px', gap: '12px' }}>
            <span style={{ fontSize: '13px', color: '#64748b' }}>
                Page {currentPage} of {totalPages}
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    style={{
                        padding: '6px 12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '4px',
                        backgroundColor: currentPage === 1 ? '#f1f5f9' : 'white',
                        color: currentPage === 1 ? '#94a3b8' : '#334155',
                        cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                        fontSize: '13px',
                        fontWeight: '500'
                    }}
                >
                    Previous
                </button>
                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    style={{
                        padding: '6px 12px',
                        border: '1px solid #e2e8f0',
                        borderRadius: '4px',
                        backgroundColor: currentPage === totalPages ? '#f1f5f9' : 'white',
                        color: currentPage === totalPages ? '#94a3b8' : '#334155',
                        cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                        fontSize: '13px',
                        fontWeight: '500'
                    }}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default PaginationControls;
