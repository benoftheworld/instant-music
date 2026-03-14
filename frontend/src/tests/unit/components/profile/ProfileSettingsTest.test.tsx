import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/components/game/VolumeControl', () => ({
  default: () => <div data-testid="volume-control">VolumeControl</div>,
}));

vi.mock('@/components/ui', () => ({
  Alert: ({ children, variant }: any) => <div data-testid={`alert-${variant}`}>{children}</div>,
}));

import ProfileSettings from '@/components/profile/ProfileSettings';

function makeUser(overrides = {}) {
  return {
    username: 'alice',
    email: 'alice@example.com',
    ...overrides,
  } as any;
}

const defaultProps = {
  activeTab: 'profile' as const,
  user: makeUser(),
  message: null,
  loading: false,
  avatarFile: null,
  avatarPreview: null,
  handleAvatarChange: vi.fn(),
  handleProfileUpdate: vi.fn(),
  passwordData: { old_password: '', new_password: '', confirm_password: '' },
  setPasswordData: vi.fn(),
  showPasswords: { old: false, new: false, confirm: false },
  setShowPasswords: vi.fn(),
  passwordMessage: null,
  handlePasswordChange: vi.fn(),
  handleExportData: vi.fn(),
  handleDeleteAccount: vi.fn(),
  showDeleteZone: false,
  setShowDeleteZone: vi.fn(),
  deleteConfirmText: '',
  setDeleteConfirmText: vi.fn(),
  passwordStrength: { score: 0, label: 'Faible', colorClass: 'text-red-500' },
  confirmMismatch: false,
};

class ProfileSettingsTest {
  run() {
    describe('ProfileSettings', () => {
      this.testProfileTabRendersForm();
      this.testShowsMessage();
    });
  }

  private testProfileTabRendersForm() {
    it('affiche le formulaire de profil', () => {
      render(<ProfileSettings {...defaultProps} />);
      expect(screen.getByText('Informations du profil')).toBeInTheDocument();
      expect(screen.getByText('Photo de profil')).toBeInTheDocument();
    });
  }

  private testShowsMessage() {
    it('affiche un message de succès', () => {
      render(
        <ProfileSettings
          {...defaultProps}
          message={{ type: 'success', text: 'Profil mis à jour' }}
        />,
      );
      expect(screen.getByText('Profil mis à jour')).toBeInTheDocument();
    });
  }
}

new ProfileSettingsTest().run();
