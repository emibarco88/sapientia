import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import DomainContextNav from "@/components/workspace/DomainContextNav";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="vnext-shell">
      <Sidebar />
      <section className="vnext-main">
        <Header />
        <DomainContextNav />
        <div className="vnext-content">{children}</div>
      </section>
    </main>
  );
}
