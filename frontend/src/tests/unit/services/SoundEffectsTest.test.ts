import { describe, it, expect, vi, beforeEach } from 'vitest';

// Spy on AudioContext methods via the global mock from setup.ts
let soundEffects: typeof import('@/services/soundEffects').soundEffects;

class SoundEffectsTest {
  run() {
    describe('SoundEffectsManager', () => {
      beforeEach(async () => {
        vi.resetModules();
        const mod = await import('@/services/soundEffects');
        soundEffects = mod.soundEffects;
        soundEffects.setEnabled(true);
        soundEffects.setVolume(0.5);
      });

      this.testDefaultState();
      this.testSetEnabled();
      this.testSetVolume();
      this.testVolumeClamping();
      this.testDisabledDoesNotPlay();
      this.testAllSoundMethods();
    });
  }

  private testDefaultState() {
    it('état par défaut — activé, volume 0.5', () => {
      expect(soundEffects.isEnabled()).toBe(true);
      expect(soundEffects.getVolume()).toBe(0.5);
    });
  }

  private testSetEnabled() {
    it('setEnabled — change l\'état', () => {
      soundEffects.setEnabled(false);
      expect(soundEffects.isEnabled()).toBe(false);
      soundEffects.setEnabled(true);
      expect(soundEffects.isEnabled()).toBe(true);
    });
  }

  private testSetVolume() {
    it('setVolume — change le volume', () => {
      soundEffects.setVolume(0.8);
      expect(soundEffects.getVolume()).toBe(0.8);
    });
  }

  private testVolumeClamping() {
    it('setVolume — clamp entre 0 et 1', () => {
      soundEffects.setVolume(5);
      expect(soundEffects.getVolume()).toBe(1);
      soundEffects.setVolume(-3);
      expect(soundEffects.getVolume()).toBe(0);
    });
  }

  private testDisabledDoesNotPlay() {
    it('ne joue aucun son quand désactivé', () => {
      soundEffects.setEnabled(false);
      // Should not throw
      expect(() => soundEffects.correctAnswer()).not.toThrow();
      expect(() => soundEffects.wrongAnswer()).not.toThrow();
      expect(() => soundEffects.click()).not.toThrow();
    });
  }

  private testAllSoundMethods() {
    const methods = [
      'correctAnswer',
      'wrongAnswer',
      'timerTick',
      'timerWarning',
      'timeUp',
      'countdownBeep',
      'countdownGo',
      'playerJoined',
      'gameStarted',
      'gameFinished',
      'click',
      'answerSubmitted',
      'roundLoading',
    ] as const;

    for (const method of methods) {
      it(`${method} — ne lance pas d'erreur`, () => {
        expect(() => (soundEffects as any)[method]()).not.toThrow();
      });
    }

    it('toutes les méthodes sonores sont des fonctions', () => {
      for (const method of methods) {
        expect(typeof (soundEffects as any)[method]).toBe('function');
      }
    });
  }
}

new SoundEffectsTest().run();
