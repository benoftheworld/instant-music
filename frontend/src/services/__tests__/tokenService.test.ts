import { describe, it, expect, beforeEach } from 'vitest';
import { tokenService } from '@/services/tokenService';

describe('tokenService', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('retourne null quand aucun token access', () => {
    expect(tokenService.getAccessToken()).toBeNull();
  });

  it('retourne null quand aucun token refresh', () => {
    expect(tokenService.getRefreshToken()).toBeNull();
  });

  it('stocke et retourne les tokens', () => {
    tokenService.setTokens('access123', 'refresh456');
    expect(tokenService.getAccessToken()).toBe('access123');
    expect(tokenService.getRefreshToken()).toBe('refresh456');
  });

  it('met a jour uniquement le token access', () => {
    tokenService.setTokens('old_access', 'refresh456');
    tokenService.setAccessToken('new_access');
    expect(tokenService.getAccessToken()).toBe('new_access');
    expect(tokenService.getRefreshToken()).toBe('refresh456');
  });

  it('supprime les deux tokens', () => {
    tokenService.setTokens('access123', 'refresh456');
    tokenService.clearTokens();
    expect(tokenService.getAccessToken()).toBeNull();
    expect(tokenService.getRefreshToken()).toBeNull();
  });
});
