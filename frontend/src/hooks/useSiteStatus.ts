import { useQuery } from '@tanstack/react-query';
import { adminService, type SiteStatus } from '@/services/adminService';

const FALLBACK: SiteStatus = {
  maintenance: false,
  maintenance_title: '',
  maintenance_message: '',
  banner: { enabled: false, message: '', color: 'info', dismissible: true },
};

/**
 * Récupère l'état du site (maintenance + bannière) avec polling toutes les 30s.
 * L'endpoint est public et exempt du middleware de maintenance.
 */
export function useSiteStatus() {
  const { data } = useQuery<SiteStatus>({
    queryKey: ['site-status'],
    queryFn: adminService.getStatus,
    staleTime: 10_000,
    refetchInterval: 30_000,
    retry: false,
  });

  return data ?? FALLBACK;
}
