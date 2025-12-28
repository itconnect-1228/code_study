import type { ReactNode } from "react";
import Header from "./Header";

interface LayoutProps {
  children: ReactNode;
}

/**
 * Layout - Main application layout wrapper
 *
 * Provides consistent layout structure with:
 * - Header with navigation and user menu
 * - Main content area
 */
export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
