import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/layout/ErrorBoundary';
import HomePage from './pages/HomePage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import GuestRoute from './components/auth/GuestRoute';
import AchievementToastManager from './components/layout/AchievementToastManager';
import { useNotificationListeners } from './hooks/useNotificationListeners';
import { useSessionRehydration } from './hooks/useSessionRehydration';

// ── Lazy-loaded pages (code splitting) ───────────────────────────────────
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage'));
const PrivacyPage = lazy(() => import('./pages/legal/PrivacyPage'));
const LegalNoticePage = lazy(() => import('./pages/legal/LegalNoticePage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const FriendsPage = lazy(() => import('./pages/FriendsPage'));
const TeamsPage = lazy(() => import('./pages/TeamsPage'));
const TeamPage = lazy(() => import('./pages/TeamPage'));
const CreateGamePage = lazy(() => import('./pages/game/CreateGamePage'));
const JoinGamePage = lazy(() => import('./pages/game/JoinGamePage'));
const GameLobbyPage = lazy(() => import('./pages/game/GameLobbyPage'));
const GamePlayPage = lazy(() => import('./pages/game/GamePlayPage'));
const GameResultsPage = lazy(() => import('./pages/game/GameResultsPage'));
const GameHistoryPage = lazy(() => import('./pages/GameHistoryPage'));
const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage'));
const ShopPage = lazy(() => import('./pages/ShopPage'));
const PublicProfilePage = lazy(() => import('./pages/PublicProfilePage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
    </div>
  );
}

function App() {
  useSessionRehydration();
  useNotificationListeners();

  return (
    <ErrorBoundary>
      <AchievementToastManager />
      <Suspense fallback={<PageLoader />}>
      <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route element={<GuestRoute />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="forgot-password" element={<ForgotPasswordPage />} />
        </Route>
        <Route path="reset-password/:uid/:token" element={<ResetPasswordPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="legal" element={<LegalNoticePage />} />
        <Route path="leaderboard" element={<LeaderboardPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="profile/:id" element={<PublicProfilePage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="friends" element={<FriendsPage />} />
          <Route path="teams" element={<TeamsPage />} />
          <Route path="teams/:id" element={<TeamPage />} />
          <Route path="history" element={<GameHistoryPage />} />
          <Route path="game/create" element={<CreateGamePage />} />
          <Route path="game/join" element={<JoinGamePage />} />
          <Route path="game/lobby/:roomCode" element={<GameLobbyPage />} />
          <Route path="game/play/:roomCode" element={<GamePlayPage />} />
          <Route path="game/:roomCode/results" element={<GameResultsPage />} />
          <Route path="shop" element={<ShopPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
    </Suspense>
    </ErrorBoundary>
  );
}

export default App;
