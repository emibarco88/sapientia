import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="app-shell">
      <Sidebar />
      <section className="app-content app-content-with-header">
        <Header />
        <div className="app-page-content">{children}</div>
      </section>
    </main>
  );
}
