import { Link, useLocation } from "wouter";
import { LayoutDashboard, Pill, FileUp, Settings } from "lucide-react";
import { InlineOrbitScore } from "@/components/orbit-score-floater";

const navItems = [
  { href: "/", label: "Home", icon: LayoutDashboard, testId: "mobile-nav-dashboard", exact: true },
  { href: "/medications", label: "Meds", icon: Pill, testId: "mobile-nav-medications", exact: false },
  { href: "/documents", label: "Docs", icon: FileUp, testId: "mobile-nav-documents", exact: false },
  { href: "/orbit-score", label: "Score", icon: null, testId: "mobile-nav-orbit-score", exact: false },
  { href: "/settings", label: "Settings", icon: Settings, testId: "mobile-nav-settings", exact: false },
];

export function MobileBottomNav() {
  const [location] = useLocation();

  return (
    <nav className="mobile-bottom-nav" data-testid="mobile-bottom-nav" aria-label="Quick navigation">
      {navItems.map((item) => {
        const isActive = item.exact
          ? location === item.href || location === "/dashboard"
          : location.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`mobile-bottom-nav-item ${isActive ? "mobile-bottom-nav-active" : ""}`}
            data-testid={item.testId}
          >
            {item.testId === "mobile-nav-orbit-score" ? (
              <InlineOrbitScore size={22} />
            ) : (
              <item.icon className="h-5 w-5" strokeWidth={isActive ? 2 : 1.5} />
            )}
            <span className="text-[10px] font-medium mt-0.5">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
