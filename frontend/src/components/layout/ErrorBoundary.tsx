import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-900 px-4">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold text-white">
              Oups, quelque chose s'est mal passé
            </h1>
            <p className="mb-6 text-gray-400">
              Une erreur inattendue est survenue. Essayez de recharger la page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="rounded-lg bg-primary-600 px-6 py-3 font-semibold text-white transition hover:bg-primary-700"
            >
              Recharger la page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
