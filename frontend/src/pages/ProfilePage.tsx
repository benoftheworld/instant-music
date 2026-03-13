import { useProfilePage, type TabId } from '@/hooks/pages/useProfilePage';
import ProfileHeader from '@/components/profile/ProfileHeader';
import ProfileStats from '@/components/profile/ProfileStats';
import ProfileAchievements from '@/components/profile/ProfileAchievements';
import ProfileSettings from '@/components/profile/ProfileSettings';

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'stats', label: 'Statistiques', icon: '📊' },
  { id: 'achievements', label: 'Succès', icon: '🏆' },
  { id: 'profile', label: 'Profil', icon: '👤' },
  { id: 'security', label: 'Sécurité', icon: '🔒' },
];

export default function ProfilePage() {
  const {
    user,
    activeTab,
    setActiveTab,
    achievementFilter,
    setAchievementFilter,
    passwordData,
    setPasswordData,
    showPasswords,
    setShowPasswords,
    avatarFile,
    avatarPreview,
    loading,
    message,
    passwordMessage,
    achievements,
    achievementsLoading,
    detailedStats,
    showDeleteZone,
    setShowDeleteZone,
    deleteConfirmText,
    setDeleteConfirmText,
    handleAvatarChange,
    handleProfileUpdate,
    handlePasswordChange,
    handleExportData,
    handleDeleteAccount,
    getAchievementProgress,
    getAchievementProgressLabel,
    filteredAchievements,
    unlockedCount,
    passwordStrength,
    confirmMismatch,
  } = useProfilePage();

  if (!user) return null;

  return (
    <div className="min-h-screen bg-cream-100">
      <div className="max-w-5xl mx-auto px-4 py-8">

        <ProfileHeader
          user={user}
          avatarPreview={avatarPreview}
          detailedStats={detailedStats}
          onAchievementsClick={() => setActiveTab('achievements')}
        />

        {/* ── Tab Navigation ───────────────────────────────────────────────── */}
        <div className="flex bg-white rounded-xl shadow-sm border border-cream-300 p-1 mb-6 gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-dark-400 hover:bg-cream-100'
              }`}
            >
              <span className="text-base">{tab.icon}</span>
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {activeTab === 'stats' && (
          <ProfileStats user={user} detailedStats={detailedStats} />
        )}

        {activeTab === 'achievements' && (
          <ProfileAchievements
            achievements={achievements}
            achievementsLoading={achievementsLoading}
            achievementFilter={achievementFilter}
            setAchievementFilter={setAchievementFilter}
            filteredAchievements={filteredAchievements}
            unlockedCount={unlockedCount}
            getAchievementProgress={getAchievementProgress}
            getAchievementProgressLabel={getAchievementProgressLabel}
          />
        )}

        {(activeTab === 'profile' || activeTab === 'security') && (
          <ProfileSettings
            activeTab={activeTab}
            user={user}
            message={message}
            loading={loading}
            avatarFile={avatarFile}
            avatarPreview={avatarPreview}
            handleAvatarChange={handleAvatarChange}
            handleProfileUpdate={handleProfileUpdate}
            passwordData={passwordData}
            setPasswordData={setPasswordData}
            showPasswords={showPasswords}
            setShowPasswords={setShowPasswords}
            passwordMessage={passwordMessage}
            handlePasswordChange={handlePasswordChange}
            handleExportData={handleExportData}
            handleDeleteAccount={handleDeleteAccount}
            showDeleteZone={showDeleteZone}
            setShowDeleteZone={setShowDeleteZone}
            deleteConfirmText={deleteConfirmText}
            setDeleteConfirmText={setDeleteConfirmText}
            passwordStrength={passwordStrength}
            confirmMismatch={confirmMismatch}
          />
        )}

      </div>
    </div>
  );
}
