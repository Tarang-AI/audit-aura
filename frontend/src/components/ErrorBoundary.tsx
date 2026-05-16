import { Component, type ErrorInfo, type ReactNode } from 'react';
import { theme } from '@/config/theme';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className={`flex flex-col items-center justify-center min-h-screen p-8 ${theme.bg.primary}`}>
          <div className={`max-w-md w-full ${theme.bg.card} rounded-lg p-8 border ${theme.border.primary}`}>
            <div className="relative">
              {/* Error icon with glow effect */}
              <div className="flex items-center justify-center w-16 h-16 mx-auto mb-6 rounded-full bg-red-500/10 border border-red-500/30">
                <svg className="w-8 h-8 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>

              <h1 className={`text-2xl font-bold mb-4 text-center ${theme.text.primary}`}>
                Something went wrong
              </h1>
              <p className={`${theme.text.secondary} mb-6 text-center text-sm`}>
                {this.state.error?.message || 'An unexpected error occurred'}
              </p>
              
              <button
                onClick={() => window.location.reload()}
                className={`w-full ${theme.button.primary} py-3 rounded-lg font-medium transition-all duration-200 hover:scale-105`}
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Made with Bob
