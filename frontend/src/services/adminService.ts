import { api } from './api';

export interface SiteBannerData {
  enabled: boolean;
  message: string;
  color: 'info' | 'success' | 'warning' | 'danger';
  dismissible: boolean;
}

export interface SiteStatus {
  maintenance: boolean;
  maintenance_title: string;
  maintenance_message: string;
  banner: SiteBannerData;
}

export const adminService = {
  /**
   * Retourne l'état du site (maintenance + bannière).
   * Endpoint public — accessible même en mode maintenance.
   */
  async getStatus(): Promise<SiteStatus> {
    const response = await api.get<SiteStatus>('/administration/status/');
    return response.data;
  },
};
