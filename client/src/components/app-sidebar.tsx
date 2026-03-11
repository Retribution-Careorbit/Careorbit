import { Link, useLocation } from "wouter";
import { useAuthStore } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import {
  Heart,
  LayoutDashboard,
  Pill,
  FileUp,
  MessageCircle,
  Bell,
  Settings,
  FlaskConical,
  LogOut,
  Moon,
  Sun,
  Target,
  Calendar,
  TrendingUp,
} from "lucide-react";

const mainNav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, testId: "nav-dashboard" },
  { href: "/orbit-score", label: "Orbit Score", icon: Target, testId: "nav-orbit-score" },
  { href: "/appointments", label: "Appointments", icon: Calendar, testId: "nav-appointments" },
  { href: "/health-insights", label: "Health Insights", icon: TrendingUp, testId: "nav-health-insights" },
];

const dataNav = [
  { href: "/medications", label: "Medications", icon: Pill, testId: "nav-medications" },
  { href: "/documents", label: "Documents", icon: FileUp, testId: "nav-documents" },
  { href: "/reminders", label: "Reminders", icon: Bell, testId: "nav-reminders" },
  { href: "/chat", label: "AI Chat", icon: MessageCircle, testId: "nav-ai-chat" },
];

const systemNav = [
  { href: "/test-cases", label: "Test Cases", icon: FlaskConical, testId: "nav-test-cases" },
  { href: "/settings", label: "Settings", icon: Settings, testId: "nav-settings" },
];

function NavItem({ item, isActive }: { item: typeof mainNav[0]; isActive: boolean }) {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={item.label}>
        <Link
          href={item.href}
          data-testid={item.testId}
          className={`flex items-center gap-3 px-3 h-[44px] rounded-xl text-sm font-medium relative ${
            isActive
              ? "nav-active-indicator text-[var(--text-primary)]"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          }`}
          style={{
            background: isActive ? "var(--accent-violet-dim)" : undefined,
            borderLeft: isActive ? "2px solid var(--accent-violet)" : "2px solid transparent",
          }}
        >
          <item.icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.5} />
          <span>{item.label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

export function AppSidebar() {
  const [location] = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const { theme, toggleTheme } = useTheme();

  return (
    <Sidebar className="scanline-overlay" style={{ background: "var(--bg-surface)", borderRight: "1px solid var(--border-subtle)" }}>
      <SidebarHeader className="h-[72px] flex items-center px-5 sidebar-header-gradient" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <Link href="/" className="flex items-center gap-2.5 group" data-testid="link-home">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{
              background: "linear-gradient(135deg, var(--accent-cyan), color-mix(in srgb, var(--accent-cyan) 80%, var(--accent-violet)))",
              boxShadow: "0 2px 8px rgba(0, 212, 255, 0.25)",
            }}
          >
            <Heart className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-mono font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
            CareOrbit
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent className="px-3 py-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {mainNav.map((item) => (
                <NavItem key={item.href} item={item} isActive={location === item.href} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-2">
          <SidebarGroupLabel className="section-header px-3 mb-1">Data</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {dataNav.map((item) => (
                <NavItem key={item.href} item={item} isActive={location === item.href} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="mt-2">
          <SidebarGroupLabel className="section-header px-3 mb-1">System</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-0.5">
              {systemNav.map((item) => (
                <NavItem key={item.href} item={item} isActive={location === item.href} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-4 py-3 flex flex-row items-center gap-3" style={{ borderTop: "1px solid var(--border-subtle)" }}>
        <div
          className="w-9 h-9 rounded-full flex items-center justify-center shrink-0"
          style={{
            background: "linear-gradient(135deg, var(--accent-violet), var(--accent-cyan))",
            boxShadow: "0 2px 8px rgba(124, 58, 237, 0.2)",
          }}
        >
          <span className="text-xs font-mono font-bold text-white">
            {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          {user?.name && (
            <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }} data-testid="text-user-name">
              {user.name}
            </p>
          )}
          <p className="text-[11px] truncate" style={{ color: "var(--text-muted)" }} data-testid="text-user-email">
            {user?.email || "User"}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="h-8 w-8 shrink-0 rounded-full"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          data-testid="button-theme-toggle"
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={logout}
          className="h-8 w-8 shrink-0 rounded-full hover:text-destructive"
          aria-label="Sign out"
          data-testid="button-sign-out-sidebar"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
