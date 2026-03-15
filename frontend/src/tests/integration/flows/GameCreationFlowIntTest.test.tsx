import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { BaseIntegrationTest } from '../base/BaseIntegrationTest';
import { seedDB, getDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import { createTestQueryClient } from '@/tests/shared/renderHelpers';
import CreateGamePage from '@/pages/game/CreateGamePage';

vi.mock('@/hooks/pages/useCreateGamePage', () => {
  let step = 1;
  let mode: string | null = null;
  return {
    useCreateGamePage: () => ({
      navigate: vi.fn(),
      loading: false,
      error: null,
      currentStep: step,
      setCurrentStep: (s: number) => { step = s; },
      selectedMode: mode,
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
      nextStep: vi.fn(() => { step = Math.min(step + 1, 4); }),
      prevStep: vi.fn(() => { step = Math.max(step - 1, 1); }),
      canProceed: () => true,
      handleCreateGame: vi.fn(),
      handleSelectMode: vi.fn((m: string) => { mode = m; }),
      handleToggleOffline: vi.fn(),
      handleSelectPlaylist: vi.fn(),
      handleSelectKaraokeSong: vi.fn(),
    }),
  };
});

class GameCreationFlowIntTest extends BaseIntegrationTest {
  run() {
    describe('Game Creation Flow (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersStep1();
      this.testShowsModeSelection();
    });
  }

  private renderApp() {
    const queryClient = createTestQueryClient();
    const user = userEvent.setup();
    const result = render(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(
          MemoryRouter,
          { initialEntries: ['/game/create'], future: { v7_relativeSplatPath: true } },
          React.createElement(
            Routes,
            null,
            React.createElement(Route, { path: '/game/create', element: React.createElement(CreateGamePage) }),
          ),
        ),
      ),
    );
    return { ...result, user };
  }

  private testRendersStep1() {
    it('affiche l\'étape 1 (mode de jeu)', () => {
      this.renderApp();
      expect(screen.getByText('Mode de jeu')).toBeInTheDocument();
    });
  }

  private testShowsModeSelection() {
    it('affiche les options de mode', () => {
      this.renderApp();
      expect(screen.getByText(/Choisissez votre mode/)).toBeInTheDocument();
    });
  }
}

new GameCreationFlowIntTest().run();
