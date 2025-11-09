import type { Metadata } from 'next';
import { ThemeProvider } from '../components/theme-provider';
import '../styles/globals.css';

export const metadata: Metadata = {
  title: 'Ask Bailey',
  description: 'Local-first interface for resume tuning and document generation.'
  ,
  icons: '/icon.png'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 font-sans text-slate-900 antialiased dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
