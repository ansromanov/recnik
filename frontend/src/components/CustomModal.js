import React from 'react';
import './CustomModal.css';

const CustomModal = ({ isOpen, onClose, onConfirm, title, message, type = 'confirm' }) => {
    const handleOverlayClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    const handleKeyDown = React.useCallback((e) => {
        if (e.key === 'Escape') {
            onClose();
        }
    }, [onClose]);

    React.useEffect(() => {
        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
            // Scroll to top when modal opens
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, handleKeyDown]);

    if (!isOpen) return null;

    return (
        <div className="custom-modal-overlay" onClick={handleOverlayClick}>
            <div className="custom-modal-content">
                <div className="custom-modal-header">
                    <h3>{title}</h3>
                    <button className="custom-modal-close" onClick={onClose}>
                        ×
                    </button>
                </div>

                <div className="custom-modal-body">
                    <p>{message}</p>
                </div>

                <div className="custom-modal-footer">
                    {type === 'confirm' ? (
                        <>
                            <button className="btn-secondary" onClick={onClose}>
                                Cancel
                            </button>
                            <button className="btn-primary" onClick={onConfirm}>
                                Confirm
                            </button>
                        </>
                    ) : (
                        <button className="btn-primary" onClick={onClose}>
                            OK
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CustomModal;
