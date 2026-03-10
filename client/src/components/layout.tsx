import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";
import { SOSButton } from "@/components/emergency";
import { OrbitScoreFloater } from "@/components/orbit-score-floater";
import { Bell, Search } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full" style={{ background: "var(--bg-base)" }}>
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          <div
            className="flex items-center gap-3 px-6 sticky top-0 z-10"
            style={{
              height: 56,
              background: "var(--bg-surface)",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <SidebarTrigger data-testid="button-sidebar-toggle" className="h-5 w-5" style={{ color: "var(--text-secondary)" }} />

            <div className="flex-1" />

            <div
              className="flex items-center gap-2 rounded-lg px-3"
              style={{
                width: 280,
                height: 36,
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-default)",
              }}
            >
              <Search className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} />
              <input
                type="text"
                placeholder="Search records, meds, docs..."
                className="flex-1 bg-transparent border-none outline-none font-mono text-xs"
                style={{ color: "var(--text-primary)" }}
                data-testid="input-header-search"
              />
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="relative h-8 w-8 rounded-lg"
              data-testid="button-notifications"
            >
              <Bell className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              <span
                className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
                style={{ background: "var(--accent-rose)" }}
              />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="h-8 w-8 rounded-lg"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              data-testid="button-theme"
            >
              {theme === "dark" ? (
                <Sun className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              ) : (
                <Moon className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              )}
            </Button>
          </div>

          <div className="p-8 lg:px-10 page-content" style={{ maxWidth: 1280, margin: "0 auto" }}>
            <PageTransition>
              {children}
            </PageTransition>
          </div>
        </main>
      </div>
      <SOSButton />
      <OrbitScoreFloater />
    </SidebarProvider>
  );
}
