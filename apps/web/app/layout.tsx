import './globals.css';
import Link from 'next/link';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="header">
          <h1>Quantum Control Plane</h1>
          <nav>
            <Link href="/experiments/new">Submit</Link>
            <Link href="/runs">Runs</Link>
            <Link href="/comparison">Comparison</Link>
          </nav>
        </header>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
