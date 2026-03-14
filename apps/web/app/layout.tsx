import './globals.css';
import Link from 'next/link';

export const metadata = {
  title: 'Quantum Control Plane',
  description: 'Quantum experiment dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <header className="bg-gray-900 text-white">
          <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
            <Link href="/experiments" className="text-lg font-semibold tracking-tight hover:text-gray-200">
              Quantum Control Plane
            </Link>
            <nav className="flex gap-6 text-sm">
              <Link href="/experiments" className="text-gray-300 hover:text-white transition-colors">
                Experiments
              </Link>
              <Link href="/experiments/new" className="text-gray-300 hover:text-white transition-colors">
                New Experiment
              </Link>
              <Link href="/runs" className="text-gray-300 hover:text-white transition-colors">
                Runs
              </Link>
              <Link href="/comparison" className="text-gray-300 hover:text-white transition-colors">
                Comparison
              </Link>
            </nav>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
