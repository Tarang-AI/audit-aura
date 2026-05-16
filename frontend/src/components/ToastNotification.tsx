import React, { useEffect, useState } from 'react';
import { X, AlertTriangle, CheckCircle, Info, AlertCircle, GitPullRequest, ExternalLink } from 'lucide-react';
import { theme } from '@/config/theme';

export interface Toast {
  id: string;
  type: 'violation' | 'success' | 'info' | 'warning' | 'pr_update';
  title: string;
  message: string;
  duration?: number;
  link?: {
    text: string;
    url: string;
  };
  prNumber?: number;
  severity?: 'critical' | 'high' | 'medium' | 'low';
}

interface ToastNotificationProps {
  toast: Toast;
  onClose: (id: string) => void;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({ toast, onClose }) => {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const duration = toast.duration || 5000;
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [toast.id]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(toast.id);
    }, 300);
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'violation':
        return <AlertTriangle className="h-5 w-5" />;
      case 'success':
        return <CheckCircle className="h-5 w-5" />;
      case 'info':
        return <Info className="h-5 w-5" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5" />;
      case 'pr_update':
        return <GitPullRequest className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getColors = () => {
    if (toast.type === 'violation' && toast.severity) {
      switch (toast.severity) {
        case 'critical':
          return `${theme.status.critical.bg} ${theme.status.critical.border} ${theme.status.critical.text}`;
        case 'high':
          return `${theme.status.high.bg} ${theme.status.high.border} ${theme.status.high.text}`;
        case 'medium':
          return `${theme.status.medium.bg} ${theme.status.medium.border} ${theme.status.medium.text}`;
        case 'low':
          return `${theme.status.low.bg} ${theme.status.low.border} ${theme.status.low.text}`;
      }
    }

    switch (toast.type) {
      case 'violation':
        return `${theme.status.critical.bg} ${theme.status.critical.border} ${theme.status.critical.text}`;
      case 'success':
        return `${theme.status.success.bg} ${theme.status.success.border} ${theme.status.success.text}`;
      case 'info':
        return `${theme.status.info.bg} ${theme.status.info.border} ${theme.status.info.text}`;
      case 'warning':
        return `${theme.status.medium.bg} ${theme.status.medium.border} ${theme.status.medium.text}`;
      case 'pr_update':
        return `${theme.status.info.bg} border-orange-500/50 text-orange-400`;
      default:
        return `${theme.bg.card} ${theme.border.primary} ${theme.text.primary}`;
    }
  };

  const getIconColor = () => {
    if (toast.type === 'violation' && toast.severity) {
      switch (toast.severity) {
        case 'critical':
          return 'text-red-600';
        case 'high':
          return 'text-orange-600';
        case 'medium':
          return 'text-yellow-600';
        case 'low':
          return 'text-cyan-400';
      }
    }

    switch (toast.type) {
      case 'violation':
        return 'text-red-600';
      case 'success':
        return 'text-green-600';
      case 'info':
        return 'text-cyan-400';
      case 'warning':
        return 'text-yellow-600';
      case 'pr_update':
        return 'text-orange-600';
      default:
        return '${theme.text.secondary}';
    }
  };

  return (
    <div
      className={`
        ${getColors()}
        ${theme.bg.card} backdrop-blur-xl
        border-l-4 rounded-lg shadow-lg p-4 mb-3 min-w-[320px] max-w-md
        transform transition-all duration-300 ease-in-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
        hover:shadow-xl hover:scale-105
      `}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div className={`flex-shrink-0 ${getIconColor()}`}>
          {getIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <p className="font-semibold text-sm mb-1">{toast.title}</p>
              <p className="text-sm opacity-90">{toast.message}</p>
              
              {toast.link && (
                <a
                  href={toast.link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-sm font-medium hover:underline"
                >
                  {toast.link.text}
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              
              {toast.prNumber && (
                <a
                  href={`/security/pr-tracking?pr=${toast.prNumber}`}
                  className="inline-flex items-center gap-1 mt-2 text-sm font-medium hover:underline"
                >
                  View PR #{toast.prNumber}
                  <GitPullRequest className="h-3 w-3" />
                </a>
              )}
            </div>
            
            <button
              onClick={handleClose}
              className={`flex-shrink-0 p-1 rounded ${theme.bg.hover} transition-colors`}
              aria-label="Close notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className={`mt-3 h-1 ${theme.border.primary} rounded-full overflow-hidden`}>
        <div
          className="h-full bg-current opacity-70 animate-progress"
          style={{
            animation: `progress ${toast.duration || 5000}ms linear forwards`
          }}
        />
      </div>
    </div>
  );
};

// Toast Container Component
interface ToastContainerProps {
  toasts: Toast[];
  onClose: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col items-end pointer-events-none">
      <div className="pointer-events-auto">
        {toasts.map((toast) => (
          <ToastNotification key={toast.id} toast={toast} onClose={onClose} />
        ))}
      </div>
    </div>
  );
};

// Toast Hook
export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const showViolation = (title: string, message: string, severity: Toast['severity'], link?: Toast['link']) => {
    addToast({
      type: 'violation',
      title,
      message,
      severity,
      link,
      duration: 8000, // Longer for violations
    });
  };

  const showPRUpdate = (prNumber: number, title: string, message: string) => {
    addToast({
      type: 'pr_update',
      title,
      message,
      prNumber,
      duration: 6000,
    });
  };

  const showSuccess = (title: string, message: string) => {
    addToast({
      type: 'success',
      title,
      message,
      duration: 4000,
    });
  };

  const showInfo = (title: string, message: string) => {
    addToast({
      type: 'info',
      title,
      message,
      duration: 5000,
    });
  };

  const showWarning = (title: string, message: string) => {
    addToast({
      type: 'warning',
      title,
      message,
      duration: 6000,
    });
  };

  return {
    toasts,
    addToast,
    removeToast,
    showViolation,
    showPRUpdate,
    showSuccess,
    showInfo,
    showWarning,
  };
};

// CSS for progress animation (add to global CSS or tailwind config)
/*
@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.animate-progress {
  animation: progress 5s linear forwards;
}
*/