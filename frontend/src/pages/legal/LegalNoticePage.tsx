import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/services/api';

interface LegalPageData {
  title: string;
  content: string;
  updated_at: string;
}

export default function LegalNoticePage() {
  const [page, setPage] = useState<LegalPageData | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/administration/legal/legal/')
      .then((r) => setPage(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <Link to="/" className="text-primary-600 hover:underline text-sm mb-6 block">
        ← Retour à l'accueil
      </Link>

      {loading && <p className="text-gray-400 italic">Chargement...</p>}

      {error && !loading && (
        <p className="text-gray-500 italic">Contenu non disponible pour le moment.</p>
      )}

      {page && (
        <>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{page.title}</h1>
          <p className="text-xs text-gray-400 mb-8">
            Dernière mise à jour :{' '}
            {new Date(page.updated_at).toLocaleDateString('fr-FR')}
          </p>
          <div className="space-y-4">
            {page.content.split('\n\n').map((para, i) => (
              <p key={i} className="text-gray-700 leading-relaxed whitespace-pre-line">
                {para}
              </p>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
