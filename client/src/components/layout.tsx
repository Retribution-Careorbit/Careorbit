import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";
import { OrbitScoreBadge } from "@/components/orbit-score-floater";
import { Bell, Search, Languages, Volume2, Square } from "lucide-react";
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

export function Layout({ children }: { children: React.ReactNode }) {
  const { theme, toggleTheme } = useTheme();
  const [location, setLocation] = useLocation();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [readLang, setReadLang] = useState<"en" | "hi">("en");
  const [isReading, setIsReading] = useState(false);
  const [isPreparingSpeech, setIsPreparingSpeech] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchInput.trim()), 300);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    const savedLang = window.localStorage.getItem("careorbit.voice.lang");
    if (savedLang === "en" || savedLang === "hi") {
      setReadLang(savedLang);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("careorbit.voice.lang", readLang);
  }, [readLang]);

  useEffect(() => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsReading(false);
  }, [location]);

  useEffect(() => {
    return () => {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const getPageReadableText = () => {
    const pageRoot = document.querySelector(".page-content");
    const raw = pageRoot?.textContent || "";
    return raw.replace(/\s+/g, " ").trim().slice(0, 5000);
  };

  const speakPage = async () => {
    if (!("speechSynthesis" in window)) return;

    if (isReading || isPreparingSpeech) {
      window.speechSynthesis.cancel();
      setIsReading(false);
      setIsPreparingSpeech(false);
      return;
    }

    const pageText = getPageReadableText();
    if (!pageText) return;

    setIsPreparingSpeech(true);
    let speechText = pageText;

    if (readLang === "hi") {
      try {
        const res = await apiRequest("POST", "/api/system/translate", {
          text: pageText,
          target_lang: "hi",
          source_lang: "en",
        });
        const data = await res.json();
        if (typeof data?.translated_text === "string" && data.translated_text.trim()) {
          speechText = data.translated_text.trim();
        }
      } catch {
        speechText = pageText;
      }
    }

    setIsPreparingSpeech(false);

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = readLang === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;
    utterance.onstart = () => setIsReading(true);
    utterance.onend = () => setIsReading(false);
    utterance.onerror = () => setIsReading(false);

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
              onClick={() => setReadLang((l) => (l === "en" ? "hi" : "en"))}
              aria-label={`Switch voice language. Current: ${readLang === "en" ? "English" : "Hindi"}`}
              data-testid="button-global-voice-language"
            >
              <Languages className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-full"
              onClick={speakPage}
              aria-label={isReading || isPreparingSpeech ? "Stop reading page" : "Read page"}
              data-testid="button-global-read-page"
            >
              {isReading || isPreparingSpeech ? (
                <Square className="h-[18px] w-[18px]" style={{ color: "var(--accent-rose)" }} />
              ) : (
                <Volume2 className="h-[18px] w-[18px]" style={{ color: "var(--text-secondary)" }} />
              )}
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
