'use client';
import { usePathname } from 'next/navigation';
import { Cormorant_Garamond, Manrope } from 'next/font/google';
import Header from '@/components/Header';
import './globals.css';

const cormorant = Cormorant_Garamond({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['500', '600', '700'],
});

const manrope = Manrope({
  subsets: ['latin'],
  variable: '--font-sans',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith('/auth');

  return (
    <html lang="en">
      <body className={`${cormorant.variable} ${manrope.variable} font-sans`}>
        {isAuthPage ? (
          <main className="min-h-screen">{children}</main>
        ) : (
          <div className="min-h-screen">
            <Header />
            <main className="mx-auto w-full max-w-[1500px] px-5 pb-10 pt-6 md:px-8 lg:px-10">{children}</main>
          </div>
        )}
      </body>
    </html>
  );
}
