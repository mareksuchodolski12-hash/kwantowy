import './globals.css';
import Link from 'next/link';

export const metadata = {
  title: 'Quantum Control Plane',
  description: 'Quantum experiment dashboard',
};

const NAV_ITEMS = [
  { href: '/experiments', label: 'Experiments' },
  { href: '/experiments/new', label: 'New Experiment' },
  { href: '/runs', label: 'Runs' },
  { href: '/comparison', label: 'Comparison' },
  { href: '/providers', label: 'Providers' },
  { href: '/demo', label: 'Demo' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-void text-text-primary min-h-screen quantum-grid">
        {/* Ambient glow blobs */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10">
          <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-accent/[0.03] blur-[120px]" />
          <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-plasma/[0.04] blur-[120px]" />
          <div className="absolute -bottom-40 left-1/3 w-[400px] h-[400px] rounded-full bg-nebula/[0.03] blur-[100px]" />
        </div>

        <header className="glass-strong sticky top-0 z-50">
          <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-3">
            <Link href="/experiments" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center group-hover:shadow-glow transition-shadow">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-accent">
                  <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3"/>
                  <circle cx="12" cy="12" r="11" stroke="currentColor" strokeWidth="1" opacity="0.4" strokeDasharray="2 4"/>
                </svg>
              </div>
              <span className="text-sm font-semibold tracking-wide text-text-primary group-hover:text-accent transition-colors">
                QCP
              </span>
            </Link>
            <nav className="flex items-center gap-1">
              {NAV_ITEMS.map(({ href, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="px-3 py-1.5 rounded-md text-xs font-medium text-text-secondary hover:text-accent hover:bg-accent/5 transition-all duration-200"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
