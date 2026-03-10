import { Spinner } from './Spinner';

interface PageLoaderProps {
  message?: string;
}

export default function PageLoader({ message = 'Chargement...' }: PageLoaderProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <Spinner size="lg" />
      <p className="mt-4 text-gray-600 text-lg">{message}</p>
    </div>
  );
}
