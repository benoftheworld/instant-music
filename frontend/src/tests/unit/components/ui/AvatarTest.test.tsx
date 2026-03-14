import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/services/api', () => ({
  getMediaUrl: (url: string | null) => url ? `http://media/${url}` : null,
}));

import Avatar from '@/components/ui/Avatar';

class AvatarTest {
  run() {
    describe('Avatar', () => {
      this.testFallbackInitial();
      this.testWithImage();
      this.testSizes();
    });
  }

  private testFallbackInitial() {
    it('sans image — affiche l\'initiale', () => {
      render(<Avatar username="alice" />);
      expect(screen.getByText('A')).toBeInTheDocument();
    });
  }

  private testWithImage() {
    it('avec image — affiche un img avec alt', () => {
      render(<Avatar src="avatar.jpg" username="bob" />);
      const img = screen.getByAltText('bob') as HTMLImageElement;
      expect(img).toBeInTheDocument();
      expect(img.src).toContain('avatar.jpg');
    });
  }

  private testSizes() {
    it.each(['sm', 'md', 'lg', 'xl'] as const)('size %s — rend sans erreur', (size) => {
      const { container } = render(<Avatar username="x" size={size} />);
      expect(container.firstChild).toBeTruthy();
    });
  }
}

new AvatarTest().run();
