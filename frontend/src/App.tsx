import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import PrivacyPage from './pages/legal/PrivacyPage';
import LegalNoticePage from './pages/legal/LegalNoticePage';
import ProfilePage from './pages/ProfilePage';
import FriendsPage from './pages/FriendsPage';
import TeamsPage from './pages/TeamsPage';
import TeamPage from './pages/TeamPage';
import CreateGamePage from './pages/game/CreateGamePage';
import JoinGamePage from './pages/game/JoinGamePage';
import GameLobbyPage from './pages/game/GameLobbyPage';
import GamePlayPage from './pages/game/GamePlayPage';
import GameResultsPage from './pages/game/GameResultsPage';
import GameHistoryPage from './pages/GameHistoryPage';
import LeaderboardPage from './pages/LeaderboardPage';
import NotFoundPage from './pages/NotFoundPage';
import ProtectedRoute from './components/auth/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="forgot-password" element={<ForgotPasswordPage />} />
        <Route path="reset-password/:uid/:token" element={<ResetPasswordPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="legal" element={<LegalNoticePage />} />
        <Route path="leaderboard" element={<LeaderboardPage />} />

        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
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
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
