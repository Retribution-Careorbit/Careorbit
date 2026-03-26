import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { PageTransition } from "@/components/animations";
import { TopNavbar } from "@/components/top-navbar";
import { MobileBottomNav } from "@/components/mobile-bottom-nav";
import { Bell, Search, Languages } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { apiRequest, queryClient } from "@/lib/queryClient";
import { useLocation } from "wouter";

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
  const { theme } = useTheme();
  const [, setLocation] = useLocation();
  const [preferredLanguage, setPreferredLanguage] = useState<string>("en");
  const lastDialogSignatureRef = useRef("");

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
    <div className="min-h-screen w-full aurora-bg">
      <TopNavbar />
      <main className="flex-1 overflow-auto">
        <div className="px-4 py-6 md:px-8 md:py-8 lg:px-10 page-content pb-24 md:pb-8" style={{ maxWidth: 1280, margin: "0 auto" }}>
          <PageTransition>
            {children}
          </PageTransition>
        </div>
      </main>
      <MobileBottomNav />
    </div>
  );
}
