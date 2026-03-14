import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/utils/format', () => ({
  formatLocalDate: () => '01/01/2026',
}));

import ProfileAchievements from '@/components/profile/ProfileAchievements';

function makeAchievement(overrides = {}) {
  return {
    id: 1,
    name: 'Premier pas',
    description: 'Jouer la première partie',
    condition_type: 'games_played',
    points: 10,
    unlocked: false,
    unlocked_at: null,
    ...overrides,
  };
}

class ProfileAchievementsTest {
  run() {
    describe('ProfileAchievements', () => {
      this.testRendersAchievements();
      this.testFilterButtons();
      this.testEmptyState();
      this.testLoadingState();
    });
  }

  private testRendersAchievements() {
    it('affiche les succès', () => {
      render(
        <ProfileAchievements
          achievements={[makeAchievement()] as any}
          achievementsLoading={false}
          achievementFilter="all"
          setAchievementFilter={() => {}}
          filteredAchievements={[makeAchievement()] as any}
          unlockedCount={0}
          getAchievementProgress={() => 50}
          getAchievementProgressLabel={() => '5/10'}
        />,
      );
      expect(screen.getByText('Premier pas')).toBeInTheDocument();
      expect(screen.getByText('10 pts')).toBeInTheDocument();
    });
  }

  private testFilterButtons() {
    it('affiche les boutons de filtre', () => {
      const setFilter = vi.fn();
      render(
        <ProfileAchievements
          achievements={[makeAchievement()] as any}
          achievementsLoading={false}
          achievementFilter="all"
          setAchievementFilter={setFilter}
          filteredAchievements={[makeAchievement()] as any}
          unlockedCount={0}
          getAchievementProgress={() => 0}
          getAchievementProgressLabel={() => null}
        />,
      );
      fireEvent.click(screen.getByText('✅ Débloqués'));
      expect(setFilter).toHaveBeenCalledWith('unlocked');
    });
  }

  private testEmptyState() {
    it('affiche "Aucun succès" si filtré vide', () => {
      render(
        <ProfileAchievements
          achievements={[makeAchievement()] as any}
          achievementsLoading={false}
          achievementFilter="unlocked"
          setAchievementFilter={() => {}}
          filteredAchievements={[]}
          unlockedCount={0}
          getAchievementProgress={() => 0}
          getAchievementProgressLabel={() => null}
        />,
      );
      expect(screen.getByText(/Aucun succès/)).toBeInTheDocument();
    });
  }

  private testLoadingState() {
    it('affiche le chargement', () => {
      render(
        <ProfileAchievements
          achievements={[]}
          achievementsLoading={true}
          achievementFilter="all"
          setAchievementFilter={() => {}}
          filteredAchievements={[]}
          unlockedCount={0}
          getAchievementProgress={() => 0}
          getAchievementProgressLabel={() => null}
        />,
      );
      expect(screen.getByText(/Chargement des succès/)).toBeInTheDocument();
    });
  }
}

new ProfileAchievementsTest().run();
