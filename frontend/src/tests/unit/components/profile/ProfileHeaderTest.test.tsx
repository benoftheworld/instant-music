import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/utils/format', () => ({
  formatLocalDate: () => 'janvier 2026',
}));

import ProfileHeader from '@/components/profile/ProfileHeader';

function makeUser(overrides = {}) {
  return {
    username: 'alice',
    created_at: '2026-01-01T00:00:00Z',
    total_games_played: 42,
    total_wins: 10,
    total_points: 1500,
    coins_balance: 200,
    ...overrides,
  } as any;
}

class ProfileHeaderTest {
  run() {
    describe('ProfileHeader', () => {
      this.testRendersUsername();
      this.testRendersStats();
      this.testRendersAchievementButton();
      this.testRendersAvatarInitial();
    });
  }

  private testRendersUsername() {
    it("affiche le nom d'utilisateur", () => {
      render(
        <ProfileHeader
          user={makeUser()}
          avatarPreview={null}
          detailedStats={null}
          onAchievementsClick={() => {}}
        />,
      );
      expect(screen.getByText('alice')).toBeInTheDocument();
    });
  }

  private testRendersStats() {
    it('affiche les stats (parties, victoires, points)', () => {
      render(
        <ProfileHeader
          user={makeUser()}
          avatarPreview={null}
          detailedStats={null}
          onAchievementsClick={() => {}}
        />,
      );
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('1500')).toBeInTheDocument();
    });
  }

  private testRendersAchievementButton() {
    it('affiche le bouton succès quand detailedStats présent', () => {
      render(
        <ProfileHeader
          user={makeUser()}
          avatarPreview={null}
          detailedStats={{ achievements_unlocked: 5, achievements_total: 20 } as any}
          onAchievementsClick={() => {}}
        />,
      );
      expect(screen.getByText('5/20')).toBeInTheDocument();
      expect(screen.getByText('Succès')).toBeInTheDocument();
    });
  }

  private testRendersAvatarInitial() {
    it("affiche l'initiale si pas d'avatar", () => {
      render(
        <ProfileHeader
          user={makeUser()}
          avatarPreview={null}
          detailedStats={null}
          onAchievementsClick={() => {}}
        />,
      );
      expect(screen.getByText('A')).toBeInTheDocument();
    });
  }
}

new ProfileHeaderTest().run();
