import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}

/** Reusable titled panel used to frame dashboard widgets. */
export function SectionCard({ title, action, children }: SectionCardProps) {
  return (
    <section className="card section-card">
      <header className="section-head">
        <h2>{title}</h2>
        {action}
      </header>
      {children}
    </section>
  );
}
