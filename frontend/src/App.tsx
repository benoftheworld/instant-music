import { useEffect } from 'react';
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
import ShopPage from './pages/ShopPage';
import NotFoundPage from './pages/NotFoundPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AchievementToastManager from './components/layout/AchievementToastManager';
import { useAuthStore } from './store/authStore';
import { notificationWS } from './services/notificationWebSocket';
import { useNotificationStore } from './store/notificationStore';
import { invitationService } from './services/invitationService';

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const addInvitation = useNotificationStore((state) => state.addInvitation);
  const setInvitations = useNotificationStore((state) => state.setInvitations);
  const clearInvitations = useNotificationStore((state) => state.clearInvitations);

  useEffect(() => {
    if (!isAuthenticated) {
      notificationWS.disconnect();
      clearInvitations();
      return;
    }

    // Fetch existing pending invitations on login/reload
    invitationService.getMyInvitations().then(setInvitations).catch(() => {});

    // Open persistent WS for real-time notifications
    notificationWS.connect();

    const unsubInvite = notificationWS.on('game_invitation', (data) => {
      if (data.invitation) {
        addInvitation(data.invitation);
        // Native browser notification (if permission granted)
        if (Notification.permission === 'granted') {
          new Notification(
            `Invitation de ${data.invitation.sender.username}`,
            {
              body: `Rejoindre la partie ${data.invitation.room_code} ?`,
              icon: '/images/logo.png',
            }
          );
        }
      }
    });

    return () => {
      unsubInvite();
    };
  }, [isAuthenticated]);

  return (
    <>
      <AchievementToastManager />
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
          <Route path="shop" element={<ShopPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
    </>
  );
}

export default App;
