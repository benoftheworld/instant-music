import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import CreateGamePage from '@/pages/game/CreateGamePage';

vi.mock('@/hooks/pages/useCreateGamePage', () => ({
  useCreateGamePage: () => ({
    navigate: vi.fn(),
    loading: false,
    error: null,
    currentStep: 1,
    setCurrentStep: vi.fn(),
    selectedMode: null,
    answerMode: 'mcq',
    setAnswerMode: vi.fn(),
    guessTarget: 'track',
    setGuessTarget: vi.fn(),
    lyricsWordsCount: 3,
    setLyricsWordsCount: vi.fn(),
    roundDuration: 30,
    setRoundDuration: vi.fn(),
    scoreDisplayDuration: 10,
    setScoreDisplayDuration: vi.fn(),
    maxPlayers: 8,
    setMaxPlayers: vi.fn(),
    numRounds: 10,
    setNumRounds: vi.fn(),
    isOnline: true,
    isPublic: false,
    setIsPublic: vi.fn(),
    isPartyMode: false,
    setIsPartyMode: vi.fn(),
    isBonusesEnabled: false,
    setIsBonusesEnabled: vi.fn(),
    selectedPlaylist: null,
    karaokeSelectedSong: null,
    isKaraoke: false,
    LAST_STEP: 4,
    nextStep: vi.fn(),
    prevStep: vi.fn(),
    canProceed: () => false,
    handleCreateGame: vi.fn(),
    handleSelectMode: vi.fn(),
    handleToggleOffline: vi.fn(),
    handleSelectPlaylist: vi.fn(),
    handleSelectKaraokeSong: vi.fn(),
  }),
}));

class CreateGamePageIntTest extends BasePageTest {
  protected getRoute() { return '/game/create'; }
  protected getComponent() { return CreateGamePage; }

  run() {
    describe('CreateGamePage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersStepOne();
      this.testRendersStepIndicator();
    });
  }

  private testRendersStepOne() {
    it('affiche le titre de l\'étape mode de jeu', () => {
      this.renderPage();
      expect(screen.getByText('Mode de jeu')).toBeInTheDocument();
    });
  }

  private testRendersStepIndicator() {
    it('affiche l\'indicateur d\'étapes', () => {
      this.renderPage();
      // Step 1 should be active
      expect(screen.getByText(/Choisissez votre mode/)).toBeInTheDocument();
    });
  }
}

new CreateGamePageIntTest().run();
