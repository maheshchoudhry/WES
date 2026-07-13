import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { StatusBadge } from '@/components/ui/StatusBadge';

describe('StatusBadge', () => {
  it('renders the status label', () => {
    render(<StatusBadge status="active" />);
    expect(screen.getByText('active')).toBeInTheDocument();
  });

  it('renders unknown statuses with a neutral tone', () => {
    render(<StatusBadge status="custom" />);
    const badge = screen.getByText('custom');
    expect(badge.className).toContain('bg-slate-100');
  });
});
