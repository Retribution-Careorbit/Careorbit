import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";
import { OrbitScoreBadge } from "@/components/orbit-score-floater";
import { Bell, Search, Languages } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useLocation } from "wouter";

interface SearchResponse {
  query: string;
  results: Array<{ id: string; type: string; title: string; subtitle: string; path: string }>;
}

interface NotificationsResponse {
  notifications: Array<{ id: string; title: string; message: string; read: boolean; path: string; created_at: string }>;
  unread_count: number;
}

interface ProfileResponse {
  profile?: {
    preferred_language?: string;
  };
}

const SPEECH_LOCALE_MAP: Record<string, string> = {
  en: "en-IN",
  hi: "hi-IN",
  bn: "bn-IN",
  ta: "ta-IN",
  te: "te-IN",
  mr: "mr-IN",
  gu: "gu-IN",
  kn: "kn-IN",
  ml: "ml-IN",
};

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();
  const [, setLocation] = useLocation();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [preferredLanguage, setPreferredLanguage] = useState<string>("en");
  const lastDialogSignatureRef = useRef("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchInput.trim()), 300);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  const { data: profileData } = useQuery<ProfileResponse>({
    queryKey: ["/api/patients/profile"],
    queryFn: async () => {
      const res = await apiRequest("GET", "/api/patients/profile");
      return res.json();
    },
    staleTime: 300_000,
  });

  useEffect(() => {
    const lang = (profileData?.profile?.preferred_language || "en").toLowerCase();
    setPreferredLanguage(lang);
  }, [profileData?.profile?.preferred_language]);

  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const translateForPatient = async (text: string) => {
    if (!text.trim()) return "";
    if (!preferredLanguage || preferredLanguage === "en") return text;
    try {
      const res = await apiRequest("POST", "/api/system/translate", {
        text,
        target_lang: preferredLanguage,
        source_lang: "en",
      });
      const data = await res.json();
      if (typeof data?.translated_text === "string" && data.translated_text.trim()) {
        return data.translated_text.trim();
      }
      return text;
    } catch {
      return text;
    }
  };

  const speakText = (text: string, lang: string) => {
    if (!("speechSynthesis" in window) || !text.trim()) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = SPEECH_LOCALE_MAP[lang] || "en-IN";
    utterance.rate = 0.95;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const { data: searchData } = useQuery<SearchResponse>({
    queryKey: ["/api/system/search", debouncedSearch],
    queryFn: async () => {
      const res = await apiRequest("GET", `/api/system/search?q=${encodeURIComponent(debouncedSearch)}`);
      return res.json();
    },
    enabled: debouncedSearch.length >= 2,
    staleTime: 10_000,
  });

  const { data: notificationsData } = useQuery<NotificationsResponse>({
    queryKey: ["/api/system/notifications"],
    refetchInterval: 10_000,
  });

  const markReadMutation = useMutation({
    mutationFn: async (ids?: string[]) => {
      const res = await apiRequest("POST", "/api/system/notifications/mark-read", { ids });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/system/notifications"] });
    },
  });

  const unreadCount = notificationsData?.unread_count || 0;
  const searchResults = searchData?.results || [];
  const hasSearchResults = debouncedSearch.length >= 2 && searchResults.length > 0;

  useEffect(() => {
    const observer = new MutationObserver(async () => {
      const dialog = document.querySelector('[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"]') as HTMLElement | null;
      if (!dialog) return;

      const text = (dialog.textContent || "").replace(/\s+/g, " ").trim();
      if (!text) return;

      const signature = text.slice(0, 800);
      if (signature === lastDialogSignatureRef.current) return;
      lastDialogSignatureRef.current = signature;

      const localized = await translateForPatient(text);
      speakText(localized, preferredLanguage);

      const existing = dialog.querySelector('[data-native-popup-summary="true"]');
      if (existing) {
        existing.remove();
      }
      const summaryBox = document.createElement("div");
      summaryBox.setAttribute("data-native-popup-summary", "true");
      summaryBox.style.marginTop = "10px";
      summaryBox.style.padding = "10px";
      summaryBox.style.border = "1px solid var(--border-default)";
      summaryBox.style.borderRadius = "10px";
      summaryBox.style.background = "var(--bg-card)";
      summaryBox.style.color = "var(--text-primary)";
      summaryBox.style.fontSize = "12px";
      summaryBox.textContent = localized;
      dialog.appendChild(summaryBox);
    });

    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [preferredLanguage]);

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full" style={{ background: "var(--bg-base)" }}>
        <AppSidebar />
        <main className="flex-1 overflow-auto">
          <div
            className="flex items-center gap-3 px-6 sticky top-0 z-10 header-bar"
          >
            <SidebarTrigger data-testid="button-sidebar-toggle" className="h-5 w-5" style={{ color: "var(--text-secondary)" }} />

            <div className="ml-1">
              <OrbitScoreBadge />
            </div>

            <div className="flex-1" />

            <div
              className="flex items-center gap-2 rounded-full px-4 relative"
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
                value={searchInput}
                onChange={(e) => {
                  setSearchInput(e.target.value);
                  setSearchOpen(true);
                }}
                onFocus={() => setSearchOpen(true)}
              />
              {searchOpen && debouncedSearch.length >= 2 && (
                <div className="absolute top-11 left-0 w-full rounded-xl p-2" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", zIndex: 30 }}>
                  {hasSearchResults ? (
                    <div className="space-y-1 max-h-72 overflow-auto">
                      {searchResults.map((result) => (
                        <button
                          key={result.id}
                          type="button"
                          className="w-full text-left p-2 rounded-lg"
                          style={{ background: "transparent" }}
                          onClick={() => {
                            setLocation(result.path || "/");
                            setSearchOpen(false);
                          }}
                        >
                          <p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{result.title}</p>
                          <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{result.subtitle}</p>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs p-2" style={{ color: "var(--text-muted)" }}>No matching records</p>
                  )}
                </div>
              )}
            </div>

            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-full"
              aria-label={`Native language: ${preferredLanguage}`}
              data-testid="button-global-voice-language"
            >
              <Languages className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="relative h-9 w-9 rounded-full"
              data-testid="button-notifications"
              onClick={() => setNotifOpen((v) => !v)}
            >
              <Bell className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              {unreadCount > 0 && (
                <span
                  className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full text-[10px] flex items-center justify-center"
                  style={{ background: "var(--accent-rose)", color: "white" }}
                >
                  {Math.min(unreadCount, 9)}
                </span>
              )}
            </Button>

            {notifOpen && (
              <div className="absolute top-14 right-16 w-80 rounded-xl p-3" style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", zIndex: 30 }}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>Notifications</p>
                  <button
                    type="button"
                    className="text-xs underline"
                    style={{ color: "var(--accent-cyan)" }}
                    onClick={() => markReadMutation.mutate(undefined)}
                  >
                    Mark all read
                  </button>
                </div>
                <div className="space-y-2 max-h-80 overflow-auto">
                  {(notificationsData?.notifications || []).length === 0 ? (
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>No notifications</p>
                  ) : (
                    (notificationsData?.notifications || []).map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        className="w-full text-left p-2 rounded-lg"
                        style={{
                          border: "1px solid var(--border-subtle)",
                          background: n.read ? "transparent" : "color-mix(in srgb, var(--accent-cyan) 8%, transparent)",
                        }}
                        onClick={() => {
                          markReadMutation.mutate([n.id]);
                          if (n.path) setLocation(n.path);
                          setNotifOpen(false);
                        }}
                      >
                        <p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{n.title}</p>
                        <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>{n.message}</p>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}

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
