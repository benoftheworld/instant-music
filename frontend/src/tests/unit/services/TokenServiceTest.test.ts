import { describe, it, expect, beforeEach } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { tokenService } from '@/services/tokenService';
import { createMockJwt, createExpiredJwt } from '@/tests/shared/factories';

class TokenServiceTest extends BaseUtilTest {
  protected name = 'tokenService';

  run() {
    describe('tokenService', () => {
      beforeEach(() => {
        tokenService.clearTokens();
      });

      this.testGetSetAccessToken();
      this.testClearTokens();
      this.testIsTokenExpiredValid();
      this.testIsTokenExpiredExpired();
      this.testIsTokenExpiredInvalid();
      this.testIsTokenExpiredCustomBuffer();
    });
  }

  private testGetSetAccessToken() {
    it('get/set access token', () => {
      expect(tokenService.getAccessToken()).toBeNull();
      tokenService.setAccessToken('abc123');
      expect(tokenService.getAccessToken()).toBe('abc123');
    });
  }

  private testClearTokens() {
    it('clearTokens remet à null', () => {
      tokenService.setAccessToken('abc');
      tokenService.clearTokens();
      expect(tokenService.getAccessToken()).toBeNull();
    });
  }

  private testIsTokenExpiredValid() {
    it('retourne false pour un token valide', () => {
      const token = createMockJwt();
      expect(tokenService.isTokenExpired(token)).toBe(false);
    });
  }

  private testIsTokenExpiredExpired() {
    it('retourne true pour un token expiré', () => {
      const token = createExpiredJwt();
      expect(tokenService.isTokenExpired(token)).toBe(true);
    });
  }

  private testIsTokenExpiredInvalid() {
    it('retourne true pour un token invalide', () => {
      expect(tokenService.isTokenExpired('not-a-jwt')).toBe(true);
      expect(tokenService.isTokenExpired('')).toBe(true);
    });
  }

  private testIsTokenExpiredCustomBuffer() {
    it('respecte le buffer personnalisé', () => {
      // Token qui expire dans 10s — avec buffer de 30s il est "expiré", avec 5s non
      const exp = Math.floor(Date.now() / 1000) + 10;
      const payload = btoa(JSON.stringify({ exp }));
      const token = `header.${payload}.sig`;
      expect(tokenService.isTokenExpired(token, 30)).toBe(true);
      expect(tokenService.isTokenExpired(token, 5)).toBe(false);
    });
  }
}

new TokenServiceTest().run();
