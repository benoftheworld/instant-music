import { useEffect, lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/layout/ErrorBoundary';
import HomePage from './pages/HomePage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import GuestRoute from './components/auth/GuestRoute';
import AchievementToastManager from './components/layout/AchievementToastManager';
import { useAuthStore } from './store/authStore';
import { notificationWS } from './services/notificationWebSocket';
import { useNotificationStore } from './store/notificationStore';
import { invitationService } from './services/invitationService';
import { friendshipService, teamService } from './services/socialService';

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
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const addInvitation = useNotificationStore((state) => state.addInvitation);
  const setInvitations = useNotificationStore((state) => state.setInvitations);
  const clearAll = useNotificationStore((state) => state.clearAll);
  const addFriendRequest = useNotificationStore((state) => state.addFriendRequest);
  const setFriendRequests = useNotificationStore((state) => state.setFriendRequests);
  const removeFriendRequest = useNotificationStore((state) => state.removeFriendRequest);
  const addSocialNotification = useNotificationStore((state) => state.addSocialNotification);

  useEffect(() => {
    if (!isAuthenticated) {
      notificationWS.disconnect();
      clearAll();
      return;
    }

    // Fetch existing pending invitations on login/reload
    invitationService.getMyInvitations().then(setInvitations).catch(() => {});

    // Fetch pending friend requests on login/reload
    friendshipService.getPendingRequests().then((reqs) => {
      setFriendRequests(reqs.map((r) => ({ id: r.id, from_user: r.from_user, created_at: r.created_at })));
    }).catch(() => {});

    // Fetch pending team join requests for teams where user is owner/admin
    teamService.getMyPendingTeamJoinRequests().then((requests) => {
      requests.forEach((req) => {
        addSocialNotification({
          id: `team-join-req-${req.id}`,
          type: 'team_join_request',
          message: `${req.user.username} veut rejoindre ${req.team.name}.`,
          link: `/teams/${req.team.id}`,
          created_at: req.created_at,
        });
      });
    }).catch(() => {});

    // Open persistent WS for real-time notifications
    notificationWS.connect();

    const unsubInvite = notificationWS.on('game_invitation', (data) => {
      if (data.invitation) {
        addInvitation(data.invitation);
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

    const unsubFriendRequest = notificationWS.on('friend_request', (data) => {
      if (data.friendship) {
        addFriendRequest({
          id: data.friendship.id,
          from_user: data.friendship.from_user,
          created_at: data.friendship.created_at,
        });
        if (Notification.permission === 'granted') {
          new Notification(`Demande d'ami de ${data.friendship.from_user.username}`, {
            body: 'Vous avez une nouvelle demande d\'ami.',
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubFriendAccepted = notificationWS.on('friend_request_accepted', (data) => {
      if (data.friendship) {
        const accepter = data.friendship.to_user;
        // Remove the pending friend request from the bell (if this user sent it)
        removeFriendRequest(data.friendship.id);
        addSocialNotification({
          id: `friend-accepted-${data.friendship.id}`,
          type: 'friend_request_accepted',
          message: `${accepter.username} a accepté votre demande d'ami.`,
          link: '/friends',
          created_at: data.friendship.updated_at || new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`${accepter.username} a accepté votre demande d'ami !`, {
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubTeamJoinRequest = notificationWS.on('team_join_request', (data) => {
      if (data.request) {
        addSocialNotification({
          id: `team-join-req-${data.request.id}`,
          type: 'team_join_request',
          message: `${data.request.user.username} veut rejoindre ${data.request.team.name}.`,
          link: `/teams/${data.request.team.id}`,
          created_at: new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`Demande d'adhésion à ${data.request.team.name}`, {
            body: `${data.request.user.username} veut rejoindre votre équipe.`,
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubTeamJoinApproved = notificationWS.on('team_join_approved', (data) => {
      if (data.approval) {
        addSocialNotification({
          id: `team-joined-${data.approval.team.id}-${Date.now()}`,
          type: 'team_join_approved',
          message: `Votre demande pour rejoindre ${data.approval.team.name} a été approuvée !`,
          link: `/teams/${data.approval.team.id}`,
          created_at: new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`Bienvenue dans ${data.approval.team.name} !`, {
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubTeamJoinRejected = notificationWS.on('team_join_rejected', (data) => {
      if (data.rejection) {
        addSocialNotification({
          id: `team-rejected-${data.rejection.team.id}-${Date.now()}`,
          type: 'team_join_rejected',
          message: `Votre demande pour rejoindre ${data.rejection.team.name} a été refusée.`,
          link: `/teams`,
          created_at: new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`Demande refusée`, {
            body: `Votre demande pour rejoindre ${data.rejection.team.name} a été refusée.`,
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubTeamRoleUpdated = notificationWS.on('team_role_updated', (data) => {
      if (data.role_update) {
        const roleLabels: Record<string, string> = { owner: 'Propriétaire', admin: 'Administrateur', member: 'Membre' };
        const newLabel = roleLabels[data.role_update.new_role] || data.role_update.new_role;
        addSocialNotification({
          id: `team-role-${data.role_update.team.id}-${Date.now()}`,
          type: 'team_role_updated',
          message: `Votre rôle dans ${data.role_update.team.name} a été mis à jour : ${newLabel}.`,
          link: `/teams/${data.role_update.team.id}`,
          created_at: new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`Rôle mis à jour dans ${data.role_update.team.name}`, {
            body: `Votre nouveau rôle : ${newLabel}.`,
            icon: '/images/logo.png',
          });
        }
      }
    });

    const unsubTeamMemberKicked = notificationWS.on('team_member_kicked', (data) => {
      if (data.kick) {
        addSocialNotification({
          id: `team-kicked-${data.kick.team.id}-${Date.now()}`,
          type: 'team_member_kicked',
          message: `Vous avez été retiré de l'équipe ${data.kick.team.name}.`,
          link: `/teams`,
          created_at: new Date().toISOString(),
        });
        if (Notification.permission === 'granted') {
          new Notification(`Retiré de ${data.kick.team.name}`, {
            body: `Vous avez été retiré de l'équipe.`,
            icon: '/images/logo.png',
          });
        }
      }
    });

    return () => {
      unsubInvite();
      unsubFriendRequest();
      unsubFriendAccepted();
      unsubTeamJoinRequest();
      unsubTeamJoinApproved();
      unsubTeamJoinRejected();
      unsubTeamRoleUpdated();
      unsubTeamMemberKicked();
    };
  }, [isAuthenticated]);

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
