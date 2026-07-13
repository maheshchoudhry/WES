import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import '@/styles/globals.css';
import { Providers } from '@/app/providers';
import { AppShell } from '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: 'WES',
  description: 'WORLD Engineering Studio — Operating System',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
