import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";
import { OrbitScoreBadge } from "@/components/orbit-score-floater";
import { Bell, Search, Heart } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";
import { Link } from "wouter";

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full" style={{ background: "var(--bg-base)" }}>
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          <div
            className="flex items-center gap-3 px-6 sticky top-0 z-10 header-bar"
          >
            <SidebarTrigger data-testid="button-sidebar-toggle" className="h-5 w-5" style={{ color: "var(--text-secondary)" }} />

            <Link href="/" className="flex items-center gap-2 ml-2" data-testid="link-home-header">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                style={{
                  background: "linear-gradient(135deg, var(--accent-cyan), color-mix(in srgb, var(--accent-cyan) 80%, var(--accent-violet)))",
                  boxShadow: "0 2px 6px rgba(0, 212, 255, 0.2)",
                }}
              >
                <Heart className="h-4 w-4 text-white" />
              </div>
              <span className="text-base font-mono font-bold tracking-tight hidden sm:inline" style={{ color: "var(--text-primary)" }}>
                CareOrbit
              </span>
            </Link>

            <div className="ml-3">
              <OrbitScoreBadge />
            </div>

            <div className="flex-1" />

            <div
              className="flex items-center gap-2 rounded-full px-4"
              style={{
                width: 280,
                height: 38,
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
              className="relative h-9 w-9 rounded-full"
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
              className="h-9 w-9 rounded-full"
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
    </SidebarProvider>
  );
}
