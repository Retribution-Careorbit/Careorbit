import { Link, useLocation } from "wouter";
import { useAuthStore } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
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
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, testId: "link-dashboard" },
  { href: "/medications", label: "Medications", icon: Pill, testId: "link-medications" },
  { href: "/documents", label: "Documents", icon: FileUp, testId: "link-documents" },
  { href: "/chat", label: "AI Chat", icon: MessageCircle, testId: "link-chat" },
  { href: "/reminders", label: "Reminders", icon: Bell, testId: "link-reminders" },
  { href: "/test-cases", label: "Test Cases", icon: FlaskConical, testId: "link-test-cases" },
  { href: "/settings", label: "Settings", icon: Settings, testId: "link-settings" },
];

export function AppSidebar() {
  const [location] = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const { theme, toggleTheme } = useTheme();

  return (
    <Sidebar>
      <SidebarHeader className="p-5 border-b border-sidebar-border">
        <Link href="/" className="flex items-center gap-2.5 group" data-testid="link-home">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
            <Heart className="h-5 w-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-heading font-bold tracking-tight">CareOrbit</span>
        </Link>
      </SidebarHeader>

      <SidebarContent className="px-3 py-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {navItems.map((item) => {
                const isActive = location === item.href;
                return (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.label}
                      className="transition-all duration-200"
                    >
                      <Link
                        href={item.href}
                        data-testid={item.testId}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/30"
                        }`}
                      >
                        <item.icon className={`h-[18px] w-[18px] transition-colors ${isActive ? "text-primary" : ""}`} />
                        <span>{item.label}</span>
                        {isActive && (
                          <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
                        )}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 border-t border-sidebar-border space-y-3">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            <span className="text-xs font-bold text-primary">
              {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            {user?.name && (
              <p className="text-sm font-medium truncate" data-testid="text-user-name">
                {user.name}
              </p>
            )}
            <p className="text-xs text-muted-foreground truncate" data-testid="text-user-email">
              {user?.email || "User"}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-8 w-8 shrink-0 rounded-lg hover:bg-accent"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            data-testid="button-theme-toggle"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
          onClick={logout}
          data-testid="button-logout"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
