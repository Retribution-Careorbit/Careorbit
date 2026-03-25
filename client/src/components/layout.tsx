import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { PageTransition } from "@/components/animations";
import { OrbitScoreBadge } from "@/components/orbit-score-floater";
import { Bell, Search, Languages, Volume2, Square, Sparkles, X } from "lucide-react";
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

const ROUTE_LABELS: Record<string, string> = {
  "/": "Dashboard",
  "/dashboard": "Dashboard",
  "/appointments": "Appointments",
  "/medications": "Medications",
  "/documents": "Documents",
  "/health-insights": "Health Insights",
  "/reminders": "Reminders",
  "/orbit-score": "Orbit Score",
  "/chat": "Chat Assistant",
  "/settings": "Settings",
};

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
  const [location, setLocation] = useLocation();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [readLang, setReadLang] = useState<string>("en");
  const [preferredLanguage, setPreferredLanguage] = useState<string>("en");
  const [isReading, setIsReading] = useState(false);
  const [isPreparingSpeech, setIsPreparingSpeech] = useState(false);
  const [entrySummary, setEntrySummary] = useState("");
  const [popupSummary, setPopupSummary] = useState("");
  const [showEntrySummary, setShowEntrySummary] = useState(false);
  const [showPopupSummary, setShowPopupSummary] = useState(false);
  const lastDialogSignatureRef = useRef("");

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearch(searchInput.trim()), 300);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    const savedLang = window.localStorage.getItem("careorbit.voice.lang");
    if (savedLang) {
      setReadLang(savedLang);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("careorbit.voice.lang", readLang);
  }, [readLang]);

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
    setReadLang(lang);
  }, [profileData?.profile?.preferred_language]);

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

    if (readLang !== "en") {
      speechText = await translateForPatient(pageText);
    }

    setIsPreparingSpeech(false);

    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.lang = SPEECH_LOCALE_MAP[readLang] || "en-IN";
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

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      const pageText = getPageReadableText();
      if (!pageText) return;
      const routeLabel = ROUTE_LABELS[location] || "CareOrbit";
      const englishSummary = `Welcome to ${routeLabel}. Here is your quick summary: ${pageText.slice(0, 450)}`;
      const localized = await translateForPatient(englishSummary);
      setEntrySummary(localized);
      setShowEntrySummary(true);
      speakText(localized, preferredLanguage);
    }, 250);

    return () => window.clearTimeout(timer);
  }, [location, preferredLanguage]);

  useEffect(() => {
    const observer = new MutationObserver(async () => {
      const dialog = document.querySelector('[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"]') as HTMLElement | null;
      if (!dialog) return;

      const text = (dialog.textContent || "").replace(/\s+/g, " ").trim();
      if (!text) return;

      const signature = text.slice(0, 800);
      if (signature === lastDialogSignatureRef.current) return;
      lastDialogSignatureRef.current = signature;

      const englishSummary = `Popup summary: ${text.slice(0, 380)}`;
      const localized = await translateForPatient(englishSummary);
      setPopupSummary(localized);
      setShowPopupSummary(true);
      speakText(localized, preferredLanguage);
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

          {showEntrySummary && entrySummary && (
            <div className="px-8 lg:px-10 pt-4" style={{ maxWidth: 1280, margin: "0 auto" }}>
              <div className="rounded-xl p-3 flex items-start justify-between gap-3" style={{ border: "1px solid var(--border-default)", background: "var(--bg-elevated)" }}>
                <div className="flex items-start gap-2">
                  <Sparkles className="h-4 w-4 mt-0.5" style={{ color: "var(--accent-cyan)" }} />
                  <p className="text-sm" style={{ color: "var(--text-primary)" }} data-testid="text-native-entry-summary">{entrySummary}</p>
                </div>
                <button type="button" onClick={() => setShowEntrySummary(false)}>
                  <X className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
                </button>
              </div>
            </div>
          )}

          {showPopupSummary && popupSummary && (
            <div className="fixed bottom-5 right-5 z-40 w-[min(90vw,420px)]" data-testid="card-native-popup-summary">
              <div className="rounded-xl p-3 shadow-lg" style={{ border: "1px solid var(--border-default)", background: "var(--bg-elevated)" }}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-medium" style={{ color: "var(--accent-cyan)" }}>Popup Summary ({preferredLanguage.toUpperCase()})</p>
                  <button type="button" onClick={() => setShowPopupSummary(false)}>
                    <X className="h-4 w-4" style={{ color: "var(--text-muted)" }} />
                  </button>
                </div>
                <p className="text-sm" style={{ color: "var(--text-primary)" }}>{popupSummary}</p>
              </div>
            </div>
          )}

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
