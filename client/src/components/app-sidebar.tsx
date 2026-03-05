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
      <SidebarHeader className="p-4">
        <Link href="/" className="flex items-center gap-2" data-testid="link-home">
          <Heart className="h-7 w-7 text-primary" />
          <span className="text-xl font-bold">CareOrbit</span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    asChild
                    isActive={location === item.href}
                    tooltip={item.label}
                  >
                    <Link href={item.href} data-testid={item.testId}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground truncate" data-testid="text-user-email">
            {user?.email || "User"}
          </span>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            data-testid="button-theme-toggle"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </div>
        <Button
          variant="outline"
          className="w-full"
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
