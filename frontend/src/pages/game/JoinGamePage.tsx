import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';

export default function JoinGamePage() {
  const navigate = useNavigate();
  const [roomCode, setRoomCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleJoinGame = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!roomCode.trim()) {
      setError('Veuillez entrer un code de salle');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Try to get the game to check if it exists
      const game = await gameService.getGame(roomCode.trim().toUpperCase());
      
      // Check if game can be joined
      if (game.status === 'finished') {
        setError('Cette partie est terminée');
        return;
      }
      
      if (game.status === 'in_progress') {
        setError('Cette partie est déjà en cours');
        return;
      }
      
      if (game.player_count >= game.max_players) {
        setError('Cette partie est complète');
        return;
      }

      // Join the game
      await gameService.joinGame(game.room_code);
      
      // Navigate to lobby
      navigate(`/game/lobby/${game.room_code}`);
    } catch (err) {
      console.error('Failed to join game:', err);
      if (err && typeof err === 'object' && 'response' in err) {
        const error = err as { response?: { status?: number } };
        if (error.response?.status === 404) {
          setError('Partie introuvable. Vérifiez le code et réessayez.');
        } else {
          setError('Erreur lors de la tentative de rejoindre la partie');
        }
      } else {
        setError('Erreur lors de la tentative de rejoindre la partie');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Retour
          </button>
          <h1 className="text-4xl font-bold mb-2">Rejoindre une partie</h1>
          <p className="text-gray-600">
            Entrez le code de salle pour rejoindre vos amis
          </p>
        </div>

        {/* Join Form */}
        <div className="card">
          <form onSubmit={handleJoinGame} className="space-y-6">
            <div>
              <label htmlFor="roomCode" className="block text-sm font-medium text-gray-700 mb-2">
                Code de salle
              </label>
              <input
                type="text"
                id="roomCode"
                value={roomCode}
                onChange={(e) => {
                  setRoomCode(e.target.value.toUpperCase());
                  setError(null);
                }}
                placeholder="ABC123"
                className="input text-center text-2xl font-bold tracking-wider"
                maxLength={6}
                disabled={loading}
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Le code de 6 caractères fourni par l'hôte de la partie
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !roomCode.trim()}
              className="btn-primary w-full text-lg"
            >
              {loading ? 'Connexion...' : 'Rejoindre la partie'}
            </button>
          </form>
        </div>

        {/* Help Section */}
        <div className="mt-8 card bg-blue-50">
          <h3 className="font-semibold text-blue-900 mb-2">💡 Besoin d'aide ?</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Demandez le code de salle à l'hôte de la partie</li>
            <li>• Le code est composé de 6 caractères</li>
            <li>• Assurez-vous que la partie n'a pas encore commencé</li>
          </ul>
        </div>

        {/* Create Game Link */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 mb-3">Vous n'avez pas de code ?</p>
          <button
            onClick={() => navigate('/game/create')}
            className="btn-secondary"
          >
            Créer votre propre partie
          </button>
        </div>
      </div>
    </div>
  );
}
