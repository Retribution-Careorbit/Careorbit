import { Link, useLocation } from "wouter";
import { useAuthStore } from "@/lib/auth";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { InlineOrbitScore } from "@/components/orbit-score-floater";
import type { SwitchablePatient } from "@/lib/patient-context";
import {
  Heart,
  LayoutDashboard,
  Pill,
  FileUp,
  MessageCircle,
  Bell,
  Settings,
  Target,
  Calendar,
  TrendingUp,
  FlaskConical,
  LogOut,
  Moon,
  Sun,
  Search,
  ChevronDown,
  Menu,
  X,
} from "lucide-react";
import { useState, useRef, useEffect, useCallback } from "react";

const primaryNav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, testId: "nav-dashboard", exact: true },
  { href: "/medications", label: "Medications", icon: Pill, testId: "nav-medications" },
  { href: "/documents", label: "Documents", icon: FileUp, testId: "nav-documents" },
  { href: "/orbit-score", label: "Orbit Score", icon: Target, testId: "nav-orbit-score" },
];

const moreNav = [
  { href: "/chat", label: "AI Chat", icon: MessageCircle, testId: "nav-ai-chat" },
  { href: "/appointments", label: "Appointments", icon: Calendar, testId: "nav-appointments" },
  { href: "/health-insights", label: "Health Insights", icon: TrendingUp, testId: "nav-health-insights" },
  { href: "/reminders", label: "Reminders", icon: Bell, testId: "nav-reminders" },
  { href: "/test-cases", label: "Test Cases", icon: FlaskConical, testId: "nav-test-cases" },
  { href: "/settings", label: "Settings", icon: Settings, testId: "nav-settings" },
];

const allNav = [...primaryNav, ...moreNav];

function isActive(location: string, href: string, exact?: boolean) {
  if (exact) return location === href || location === "/dashboard";
  return location.startsWith(href);
}

function MoreDropdown({ location }: { location: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setOpen(false);
      buttonRef.current?.focus();
    }
  }, []);

  const anyActive = moreNav.some((item) => isActive(location, item.href));

  return (
    <div ref={ref} className="relative" onKeyDown={handleKeyDown}>
      <button
        ref={buttonRef}
        onClick={() => setOpen(!open)}
        className={`topnav-link flex items-center gap-1 ${anyActive ? "topnav-link-active" : ""}`}
        data-testid="nav-more-dropdown"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="More navigation options"
      >
        More
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div
          className="absolute top-full right-0 mt-2 w-52 rounded-xl py-2 z-50"
          role="menu"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-default)",
            boxShadow: "0 12px 40px rgba(0,0,0,0.15)",
          }}
        >
          {moreNav.map((item) => {
            const active = isActive(location, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                data-testid={item.testId}
                role="menuitem"
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  active
                    ? "font-medium"
                    : "hover:bg-[var(--bg-hover)]"
                }`}
                style={{ color: active ? "var(--accent-cyan)" : "var(--text-secondary)" }}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MobileMenuSheet({
  location,
  onClose,
  members,
  activePatientId,
  onSwitchPatient,
}: {
  location: string;
  onClose: () => void;
  members: SwitchablePatient[];
  activePatientId: string;
  onSwitchPatient: (patientId: string) => void;
}) {
  const { theme, toggleTheme } = useTheme();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const activeMemberName = members.find((m) => m.id === activePatientId)?.name || user?.name || "User";
  const activeMemberInitial = activeMemberName?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U";

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  return (
    <div className="fixed inset-0 z-[60]" data-testid="mobile-menu-overlay">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div
        className="absolute top-0 right-0 h-full w-72 overflow-y-auto"
        style={{
          background: "var(--bg-surface)",
          borderLeft: "1px solid var(--border-subtle)",
          animation: "slideInRight 200ms ease forwards",
        }}
        role="dialog"
        aria-label="Navigation menu"
      >
        <div className="flex items-center justify-between p-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, var(--accent-violet), var(--accent-cyan))" }}
            >
              <span className="text-xs font-mono font-bold text-white">
                {activeMemberInitial}
              </span>
            </div>
            <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              {activeMemberName}
            </span>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[var(--bg-hover)]" aria-label="Close menu" data-testid="button-close-mobile-menu">
            <X className="h-5 w-5" style={{ color: "var(--text-secondary)" }} />
          </button>
        </div>
        <nav className="p-3" aria-label="Main navigation">
          {members.length > 1 && (
            <div className="mb-2 px-1">
              <p className="text-xs uppercase tracking-wide mb-2" style={{ color: "var(--text-muted)" }}>
                Active Member
              </p>
              <div className="space-y-1">
                {members.map((member) => {
                  const active = member.id === activePatientId;
                  return (
                    <button
                      key={member.id}
                      type="button"
                      onClick={() => {
                        onSwitchPatient(member.id);
                        onClose();
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${active ? "font-medium" : "hover:bg-[var(--bg-hover)]"}`}
                      style={{ color: active ? "var(--accent-cyan)" : "var(--text-secondary)" }}
                      data-testid={`mobile-member-${member.id}`}
                    >
                      {member.name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          {allNav.map((item) => {
            const active = isActive(location, item.href, (item as any).exact);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                data-testid={`mobile-menu-${item.testId}`}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors mb-0.5 ${
                  active ? "font-medium" : "hover:bg-[var(--bg-hover)]"
                }`}
                style={{ color: active ? "var(--accent-cyan)" : "var(--text-secondary)" }}
              >
                <item.icon className="h-4.5 w-4.5" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 mt-2" style={{ borderTop: "1px solid var(--border-subtle)" }}>
          <button
            onClick={() => { toggleTheme(); }}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm w-full hover:bg-[var(--bg-hover)] transition-colors"
            style={{ color: "var(--text-secondary)" }}
            data-testid="mobile-menu-theme-toggle"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            {theme === "dark" ? "Light Mode" : "Dark Mode"}
          </button>
          <button
            onClick={() => { logout(); onClose(); }}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm w-full hover:bg-[var(--bg-hover)] transition-colors text-destructive"
            data-testid="mobile-menu-sign-out"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

export function TopNavbar({
  members = [],
  activePatientId,
  onSwitchPatient,
}: {
  members?: SwitchablePatient[];
  activePatientId: string;
  onSwitchPatient: (patientId: string) => void;
}) {
  const [location] = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const activeMemberName = members.find((m) => m.id === activePatientId)?.name || user?.name || "User";
  const activeMemberInitial = activeMemberName?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U";

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location]);

  return (
    <>
      <header className="topnav" data-testid="topnav">
        <div className="topnav-inner">
          <div className="flex items-center gap-4 lg:gap-6 xl:gap-8 min-w-0">
            <Link href="/" className="flex items-center gap-2 shrink-0" data-testid="link-home">
              <div
                className="w-8 h-8 lg:w-9 lg:h-9 rounded-xl flex items-center justify-center"
                style={{
                  background: "linear-gradient(135deg, var(--accent-cyan), color-mix(in srgb, var(--accent-cyan) 80%, var(--accent-violet)))",
                  boxShadow: "0 2px 12px rgba(0, 212, 255, 0.25)",
                }}
              >
                <Heart className="h-4 w-4 lg:h-5 lg:w-5 text-white" />
              </div>
              <span className="text-base lg:text-lg font-mono font-bold tracking-tight" style={{ color: "var(--text-primary)" }}>
                CareOrbit
              </span>
            </Link>

            <nav className="hidden md:flex min-w-0 items-center gap-0.5 lg:gap-1" aria-label="Main navigation" data-testid="topnav-links">
              {primaryNav.map((item) => {
                const active = isActive(location, item.href, item.exact);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    data-testid={item.testId}
                    className={`topnav-link ${active ? "topnav-link-active" : ""}`}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                    {item.testId === "nav-orbit-score" && <InlineOrbitScore />}
                  </Link>
                );
              })}
              <MoreDropdown location={location} />
            </nav>
          </div>

          <div className="flex items-center gap-1.5 lg:gap-2 shrink-0">

            <div
              className="hidden 2xl:flex items-center gap-2 rounded-full px-3"
              style={{
                width: 190,
                height: 34,
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-default)",
              }}
            >
              <Search className="h-4 w-4 shrink-0" style={{ color: "var(--text-muted)" }} />
              <input
                type="text"
                placeholder="Search..."
                className="flex-1 bg-transparent border-none outline-none text-xs"
                style={{ color: "var(--text-primary)" }}
                data-testid="input-header-search"
              />
            </div>

            <span className="md:hidden">
              <InlineOrbitScore size={22} />
            </span>

            <Button
              variant="ghost"
              size="icon"
              className="relative h-9 w-9 rounded-full"
              data-testid="button-notifications"
              aria-label="Notifications"
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
              className="h-9 w-9 rounded-full hidden md:flex"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              data-testid="button-theme"
            >
              {theme === "dark" ? (
                <Sun className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              ) : (
                <Moon className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(true)}
              className="h-9 w-9 rounded-full md:hidden"
              aria-label="Open navigation menu"
              data-testid="button-mobile-menu"
            >
              <Menu className="h-5 w-5" style={{ color: "var(--text-secondary)" }} />
            </Button>

            <div className="hidden md:flex items-center gap-2 ml-2 pl-3" style={{ borderLeft: "1px solid var(--border-subtle)" }}>
              {members.length > 1 && (
                <div
                  className="hidden 2xl:flex relative items-center h-9 rounded-full px-2.5 shrink-0"
                  style={{
                    minWidth: 200,
                    maxWidth: 220,
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-default)",
                  }}
                  title={activeMemberName}
                >
                  <select
                    value={activePatientId}
                    onChange={(e) => onSwitchPatient(e.target.value)}
                    className="w-full bg-transparent text-xs font-medium outline-none appearance-none pr-6"
                    style={{ color: "var(--text-primary)", textOverflow: "ellipsis" }}
                    data-testid="select-active-member"
                  >
                    {members.map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="h-3.5 w-3.5 absolute right-2.5 pointer-events-none" style={{ color: "var(--text-muted)" }} />
                </div>
              )}

              <Link href="/settings" data-testid="link-profile-avatar">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 cursor-pointer transition-opacity hover:opacity-80"
                  style={{
                    background: "linear-gradient(135deg, var(--accent-violet), var(--accent-cyan))",
                  }}
                >
                  <span className="text-xs font-mono font-bold text-white">
                    {activeMemberInitial}
                  </span>
                </div>
              </Link>
              <div className="min-w-0 hidden 2xl:block">
                <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }} data-testid="text-user-name">
                  {activeMemberName}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={logout}
                className="h-8 w-8 shrink-0 rounded-full hover:text-destructive"
                aria-label="Sign out"
                data-testid="button-sign-out"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>
      {mobileMenuOpen && (
        <MobileMenuSheet
          location={location}
          onClose={() => setMobileMenuOpen(false)}
          members={members}
          activePatientId={activePatientId}
          onSwitchPatient={onSwitchPatient}
        />
      )}
    </>
  );
}
