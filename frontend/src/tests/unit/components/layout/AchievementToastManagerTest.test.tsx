import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';

const { mockOn } = vi.hoisted(() => ({ mockOn: vi.fn() }));

vi.mock('@/services/notificationWebSocket', () => ({
  notificationWS: { on: mockOn },
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn((selector: any) => selector({ isAuthenticated: true })),
}));

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url,
}));

import AchievementToastManager from '@/components/layout/AchievementToastManager';

class AchievementToastManagerTest {
  run() {
    describe('AchievementToastManager', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
      });

      this.testRendersNothingInitially();
      this.testShowsToastOnEvent();
    });
  }

  private testRendersNothingInitially() {
    it('ne rend rien sans toast', () => {
      mockOn.mockReturnValue(() => {});
      const { container } = render(<AchievementToastManager />);
      expect(container.innerHTML).toBe('');
    });
  }

  private testShowsToastOnEvent() {
    it('affiche un toast quand achievement_unlocked est reçu', () => {
      let achievementCallback: ((data: any) => void) | undefined;
      mockOn.mockImplementation((event: string, cb: any) => {
        if (event === 'achievement_unlocked') achievementCallback = cb;
        return () => {};
      });

      render(<AchievementToastManager />);

      act(() => {
        achievementCallback?.({
          achievement: {
            id: '1',
            name: 'Premier pas',
            description: 'Jouer une première partie',
            icon: null,
            points: 10,
          },
        });
      });

      expect(screen.getByText('Succès débloqué !')).toBeInTheDocument();
      expect(screen.getByText('Premier pas')).toBeInTheDocument();
      expect(screen.getByText('+10 pts')).toBeInTheDocument();

      vi.useRealTimers();
    });
  }
}

new AchievementToastManagerTest().run();
