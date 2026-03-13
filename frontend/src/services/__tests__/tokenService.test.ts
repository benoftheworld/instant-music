import { describe, it, expect, beforeEach } from 'vitest';
import { tokenService } from '@/services/tokenService';

describe('tokenService', () => {
  beforeEach(() => {
    tokenService.clearTokens();
  });

  it('retourne null quand aucun token access', () => {
    expect(tokenService.getAccessToken()).toBeNull();
  });

  it('stocke et retourne le access token en memoire', () => {
    tokenService.setAccessToken('access123');
    expect(tokenService.getAccessToken()).toBe('access123');
  });

  it('met a jour le token access', () => {
    tokenService.setAccessToken('old_access');
    tokenService.setAccessToken('new_access');
    expect(tokenService.getAccessToken()).toBe('new_access');
  });

  it('supprime le token', () => {
    tokenService.setAccessToken('access123');
    tokenService.clearTokens();
    expect(tokenService.getAccessToken()).toBeNull();
  });
});
