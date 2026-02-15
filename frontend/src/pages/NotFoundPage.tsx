import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <p className="text-xl text-gray-600 mb-8">Page non trouvée</p>
        <Link to="/" className="btn-primary">
          Retour à l'accueil
        </Link>
      </div>
    </div>
  );
}
