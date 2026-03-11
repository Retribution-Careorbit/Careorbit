import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/layout";
import { useToast } from "@/hooks/use-toast";
import { FadeIn } from "@/components/animations";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Globe, AlertTriangle, Lightbulb } from "lucide-react";

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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
      toast({ title: "Error", description: err.message, variant: "destructive" });
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

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <FadeIn>
          <div className="page-title-bar">
            <div>
              <h1 data-testid="text-chat-title">
                AI Health Assistant
              </h1>
              <p>
                Ask about medications, screenings, or your health history
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setLanguage((l) => (l === "en" ? "hi" : "en"))}
              data-testid="button-language-toggle"
            >
              <Globe className="h-4 w-4 mr-2" />
              {language === "en" ? "English" : "हिन्दी"}
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
                    {language === "en" ? "How can I help you today?" : "मैं आज आपकी कैसे मदद कर सकता हूँ?"}
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {["What medications am I taking?", "Any drug interactions?", "Am I due for screenings?"].map((q) => (
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
                              {msg.alerts.length} alert(s)
                            </div>
                          )}
                          {msg.care_gaps && msg.care_gaps.length > 0 && (
                            <div className="flex items-center gap-1 text-xs" style={{ color: "var(--accent-amber)" }}>
                              <Lightbulb className="h-3 w-3" />
                              {msg.care_gaps.length} care gap(s)
                            </div>
                          )}
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
                  <span className="text-xs font-medium" style={{ color: "var(--accent-cyan)" }}>CareOrbit AI</span>
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
              <input
                type="text"
                placeholder={language === "en" ? "Type your health question..." : "अपना स्वास्थ्य प्रश्न टाइप करें..."}
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
                aria-label="Send message"
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
