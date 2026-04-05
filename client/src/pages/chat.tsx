import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useActivePatientStore } from "@/lib/patient-context";
import { useToast } from "@/hooks/use-toast";
import { FadeIn } from "@/components/animations";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Globe, AlertTriangle, Lightbulb, Volume2, Square, Mic } from "lucide-react";

declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  language?: string;
  agents_used?: string[];
  alerts?: any[];
  care_gaps?: any[];
  confidence?: number;
  timestamp?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const { toast } = useToast();
  const activePatientId = useActivePatientStore((s) => s.activePatientId);

  const { data: profileData } = useQuery<any>({
    queryKey: ["/api/patients/profile", activePatientId],
  });

  const isHindi = String(profileData?.profile?.preferred_language || "en").toLowerCase() === "hi";

  useEffect(() => {
    if (isHindi) {
      setLanguage("hi");
    }
  }, [isHindi]);

  const t = {
    title: isHindi ? "एआई स्वास्थ्य सहायक" : "AI Health Assistant",
    subtitle: isHindi ? "दवाइयों, स्क्रीनिंग या स्वास्थ्य इतिहास के बारे में पूछें" : "Ask about medications, screenings, or your health history",
    english: isHindi ? "अंग्रेज़ी" : "English",
    hindi: "हिन्दी",
    playVoice: isHindi ? "आवाज़ चलाएँ" : "Play Voice",
    stopVoice: isHindi ? "आवाज़ रोकें" : "Stop Voice",
    alertCount: isHindi ? "अलर्ट" : "alert(s)",
    careGapCount: isHindi ? "केयर गैप" : "care gap(s)",
    aiTyping: isHindi ? "केयरऑर्बिट एआई" : "CareOrbit AI",
    error: isHindi ? "त्रुटि" : "Error",
    voiceUnavailable: isHindi ? "आवाज़ सुविधा उपलब्ध नहीं" : "Voice unavailable",
    ttsNotSupported: isHindi ? "इस ब्राउज़र में टेक्स्ट-टू-स्पीच समर्थित नहीं है।" : "Text-to-speech is not supported in this browser.",
    voicePlaybackFailed: isHindi ? "आवाज़ चलाने में विफल" : "Voice playback failed",
    voicePlaybackFailedDesc: isHindi ? "सहायक की आवाज़ प्रतिक्रिया नहीं चल सकी।" : "Could not play assistant voice response.",
    sttNotSupported: isHindi ? "इस ब्राउज़र में स्पीच रिकग्निशन समर्थित नहीं है।" : "Speech recognition is not supported in this browser.",
    voiceInputFailed: isHindi ? "आवाज़ इनपुट विफल" : "Voice input failed",
    voiceInputFailedDesc: isHindi ? "आवाज़ कैप्चर नहीं हो सकी। कृपया फिर से प्रयास करें।" : "Could not capture voice. Please try again.",
    voiceCaptured: isHindi ? "आवाज़ कैप्चर हुई" : "Voice captured",
    voiceCapturedDesc: isHindi ? "ट्रांसक्राइब संदेश की समीक्षा करें और भेजें।" : "Review and send your transcribed message.",
    stopVoiceInput: isHindi ? "वॉइस इनपुट रोकें" : "Stop voice input",
    startVoiceInput: isHindi ? "वॉइस इनपुट शुरू करें" : "Start voice input",
    sendMessage: isHindi ? "संदेश भेजें" : "Send message",
    emptyPrompt: isHindi ? "मैं आज आपकी कैसे मदद कर सकता हूँ?" : "How can I help you today?",
    quickQs: isHindi
      ? ["मैं कौन-कौन सी दवाइयाँ ले रहा हूँ?", "क्या कोई दवा इंटरैक्शन है?", "क्या मेरी कोई स्क्रीनिंग देय है?"]
      : ["What medications am I taking?", "Any drug interactions?", "Am I due for screenings?"],
    inputPlaceholder: isHindi ? "अपना स्वास्थ्य प्रश्न टाइप करें..." : "Type your health question...",
  };

  const supportsSpeechSynthesis = typeof window !== "undefined" && "speechSynthesis" in window;
  const supportsSpeechRecognition = typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (supportsSpeechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [supportsSpeechSynthesis]);

  const chatMutation = useMutation({
    mutationFn: async (body: { message: string; language: string }) => {
      const res = await apiRequest("POST", "/api/chat/query", body);
      return res.json();
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message,
          language: data.language,
          agents_used: data.agents_used,
          alerts: data.alerts,
          care_gaps: data.care_gaps,
          confidence: data.confidence,
          timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    },
    onError: (err: Error) => {
      toast({ title: t.error, description: err.message, variant: "destructive" });
    },
  });

  const sendMessage = () => {
    if (!input.trim() || chatMutation.isPending) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, {
      role: "user",
      content: userMsg,
      timestamp: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    }]);
    chatMutation.mutate({ message: userMsg, language });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resolveSpeechLang = (lang: string | undefined) => {
    if (lang === "hi") return "hi-IN";
    return "en-IN";
  };

  const speakMessage = (content: string, msgLang: string | undefined, index: number) => {
    if (!supportsSpeechSynthesis) {
      toast({ title: t.voiceUnavailable, description: t.ttsNotSupported });
      return;
    }

    if (speakingIndex === index) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(content);
    utterance.lang = resolveSpeechLang(msgLang || language);
    utterance.rate = 0.95;
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => {
      setSpeakingIndex(null);
      toast({ title: t.voicePlaybackFailed, description: t.voicePlaybackFailedDesc, variant: "destructive" });
    };
    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  };

  const startVoiceInput = () => {
    if (!supportsSpeechRecognition) {
      toast({ title: t.voiceUnavailable, description: t.sttNotSupported });
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }

    const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new RecognitionCtor();
    recognition.lang = resolveSpeechLang(language);
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => {
      setIsListening(false);
      toast({ title: t.voiceInputFailed, description: t.voiceInputFailedDesc, variant: "destructive" });
    };
    recognition.onresult = (event: any) => {
      const transcript = event?.results?.[0]?.[0]?.transcript?.trim() || "";
      if (!transcript) return;
      setInput(transcript);
      toast({ title: t.voiceCaptured, description: t.voiceCapturedDesc });
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-chat-title">
                {t.title}
              </h1>
              <p>
                {t.subtitle}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setLanguage((l) => (l === "en" ? "hi" : "en"))}
              data-testid="button-language-toggle"
            >
              <Globe className="h-4 w-4 mr-2" />
              {language === "en" ? t.english : t.hindi}
            </Button>
          </div>
        </FadeIn>

        <div
          className="flex-1 overflow-hidden flex flex-col page-card mt-2"
        >
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-center">
                <div className="space-y-4">
                  <div
                    className="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto"
                    style={{
                      background: "linear-gradient(135deg, var(--accent-cyan-dim), var(--accent-violet-dim))",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <Bot className="h-10 w-10" style={{ color: "var(--accent-cyan)", opacity: 0.6 }} />
                  </div>
                  <p className="text-lg font-medium" style={{ color: "var(--text-primary)" }} data-testid="text-chat-empty">
                    {t.emptyPrompt}
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {t.quickQs.map((q) => (
                      <Button
                        key={q}
                        variant="outline"
                        size="sm"
                        onClick={() => setInput(q)}
                        className="text-xs rounded-full"
                        data-testid={`button-suggestion-${q.slice(0, 10).replace(/\s/g, "-")}`}
                      >
                        {q}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <AnimatePresence mode="popLayout">
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 12, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.25, ease: "easeOut" }}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  data-testid={`chat-message-${i}`}
                >
                  {msg.role === "assistant" && (
                    <div
                      className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                      style={{
                        background: "linear-gradient(135deg, var(--accent-cyan-dim), var(--accent-violet-dim))",
                      }}
                    >
                      <Bot className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
                    </div>
                  )}
                  <div className="max-w-[75%]">
                    <div
                      className="p-3.5 px-4"
                      style={{
                        borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                        background: msg.role === "user"
                          ? "linear-gradient(135deg, var(--accent-violet-dim), color-mix(in srgb, var(--accent-violet-dim) 80%, var(--accent-cyan-dim)))"
                          : "var(--bg-elevated)",
                        border: msg.role === "user"
                          ? "1px solid rgba(124, 58, 237, 0.20)"
                          : "1px solid var(--border-subtle)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                      {msg.role === "assistant" && (
                        <div className="mt-2 space-y-1">
                          {msg.agents_used && msg.agents_used.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {msg.agents_used.map((a) => (
                                <Badge key={a} variant="outline" className="text-xs">{a}</Badge>
                              ))}
                            </div>
                          )}
                          {msg.alerts && msg.alerts.length > 0 && (
                            <div className="flex items-center gap-1 text-xs" style={{ color: "var(--accent-rose)" }}>
                              <AlertTriangle className="h-3 w-3" />
                              {msg.alerts.length} {t.alertCount}
                            </div>
                          )}
                          {msg.care_gaps && msg.care_gaps.length > 0 && (
                            <div className="flex items-center gap-1 text-xs" style={{ color: "var(--accent-amber)" }}>
                              <Lightbulb className="h-3 w-3" />
                              {msg.care_gaps.length} {t.careGapCount}
                            </div>
                          )}
                          <div>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              className="h-7 px-2 text-[11px]"
                              onClick={() => speakMessage(msg.content, msg.language, i)}
                              data-testid={`button-voice-read-${i}`}
                            >
                              {speakingIndex === i ? <Square className="h-3 w-3 mr-1" /> : <Volume2 className="h-3 w-3 mr-1" />}
                              {speakingIndex === i ? t.stopVoice : t.playVoice}
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                    {msg.timestamp && (
                      <p className="font-mono text-[10px] mt-1 px-1" style={{ color: "var(--text-muted)" }}>
                        {msg.timestamp}
                      </p>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div
                      className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                      style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)" }}
                    >
                      <User className="h-4 w-4" style={{ color: "var(--text-secondary)" }} />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {chatMutation.isPending && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-3" data-testid="typing-indicator">
                <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: "var(--accent-cyan-dim)" }}>
                  <Bot className="h-4 w-4" style={{ color: "var(--accent-cyan)" }} />
                </div>
                <div className="flex items-center gap-2 px-4 py-2">
                  <span className="text-xs font-medium" style={{ color: "var(--accent-cyan)" }}>{t.aiTyping}</span>
                  <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: "var(--accent-cyan)" }} />
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div
            className="px-5 py-4"
            style={{ borderTop: "1px solid var(--border-subtle)", background: "var(--bg-surface)" }}
          >
            <div className="flex gap-2">
              <button
                type="button"
                onClick={startVoiceInput}
                className="h-11 w-11 rounded-full flex items-center justify-center shrink-0 disabled:opacity-50"
                style={{
                  background: isListening
                    ? "linear-gradient(135deg, var(--accent-rose), color-mix(in srgb, var(--accent-rose) 80%, var(--accent-amber)))"
                    : "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                  color: isListening ? "white" : "var(--text-secondary)",
                }}
                aria-label={isListening ? t.stopVoiceInput : t.startVoiceInput}
                data-testid="button-voice-input"
              >
                {isListening ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </button>
              <input
                type="text"
                placeholder={t.inputPlaceholder}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 h-11 px-5 rounded-full bg-transparent outline-none text-sm"
                style={{
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border-default)",
                  color: "var(--text-primary)",
                }}
                data-testid="input-chat"
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || chatMutation.isPending}
                className="h-11 w-11 rounded-full flex items-center justify-center shrink-0 disabled:opacity-50"
                style={{
                  background: "linear-gradient(135deg, var(--accent-cyan), color-mix(in srgb, var(--accent-cyan) 80%, var(--accent-violet)))",
                  color: "white",
                  boxShadow: "0 2px 8px rgba(0, 212, 255, 0.3)",
                }}
                aria-label={t.sendMessage}
                data-testid="button-send"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
