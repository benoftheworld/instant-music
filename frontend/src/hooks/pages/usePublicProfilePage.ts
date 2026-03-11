import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { statsService } from '@/services/statsService';
import type { UserPublicProfile } from '@/types';

export function usePublicProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = useAuthStore((s) => s.user);
  const [profile, setProfile] = useState<UserPublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect to own profile page if viewing self
  useEffect(() => {
    if (id && currentUser && id === String(currentUser.id)) {
      navigate('/profile', { replace: true });
    }
  }, [id, currentUser, navigate]);

  useEffect(() => {
    if (!id) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const profileData = await statsService.getUserStats(id);
        setProfile(profileData);
      } catch {
        setError('Impossible de charger le profil.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  return {
    navigate,
    profile,
    loading,
    error,
  };
}
