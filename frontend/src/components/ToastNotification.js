import React, { useState, useEffect } from 'react';
import './CustomModal.css';

const ToastNotification = ({ message, type = 'success', duration = 4000, onClose }) => {
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsVisible(false);
            setTimeout(onClose, 300); // Wait for animation to complete
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    if (!isVisible) return null;

    const getTitle = () => {
        switch (type) {
            case 'success': return 'Success';
            case 'error': return 'Error';
            case 'warning': return 'Warning';
            case 'info': return 'Info';
            default: return 'Notification';
        }
    };

    const handleClose = () => {
        setIsVisible(false);
        setTimeout(onClose, 300);
    };

    return (
        <div className={`toast-notification ${type}`}>
            <div className="toast-header">
                <h4 className="toast-title">{getTitle()}</h4>
                <button className="toast-close" onClick={handleClose}>
                    ×
                </button>
            </div>
            <p className="toast-message">{message}</p>
        </div>
    );
};

// Toast manager to handle multiple toasts
export const useToast = () => {
    const [toasts, setToasts] = useState([]);

    const showToast = (message, type = 'success', duration = 4000) => {
        const id = Date.now();
        const newToast = { id, message, type, duration };

        setToasts(prev => [...prev, newToast]);
    };

    const removeToast = (id) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    };

    const ToastContainer = () => (
        <div style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 1001 }}>
            {toasts.map((toast, index) => (
                <div key={toast.id} style={{ marginBottom: '10px', marginTop: index > 0 ? '10px' : '0' }}>
                    <ToastNotification
                        message={toast.message}
                        type={toast.type}
                        duration={toast.duration}
                        onClose={() => removeToast(toast.id)}
                    />
                </div>
            ))}
        </div>
    );

    return { showToast, ToastContainer };
};

export default ToastNotification;
