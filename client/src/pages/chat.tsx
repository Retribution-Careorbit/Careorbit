import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
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
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-heading font-bold tracking-tight" data-testid="text-chat-title">AI Health Assistant</h1>
              <p className="text-muted-foreground mt-1">
                Ask about medications, screenings, or your health history
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setLanguage((l) => (l === "en" ? "hi" : "en"))}
              className="shadow-sm"
              data-testid="button-language-toggle"
            >
              <Globe className="h-4 w-4 mr-2" />
              {language === "en" ? "English" : "हिन्दी"}
            </Button>
          </div>
        </FadeIn>

        <Card className="flex-1 overflow-hidden flex flex-col">
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-center">
                <div className="space-y-4">
                  <div className="w-20 h-20 rounded-full bg-primary/5 flex items-center justify-center mx-auto">
                    <Bot className="h-10 w-10 text-primary/40" />
                  </div>
                  <p className="text-lg font-heading font-medium" data-testid="text-chat-empty">
                    {language === "en"
                      ? "How can I help you today?"
                      : "मैं आज आपकी कैसे मदद कर सकता हूँ?"}
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {["What medications am I taking?", "Any drug interactions?", "Am I due for screenings?"].map((q) => (
                      <Button
                        key={q}
                        variant="outline"
                        size="sm"
                        onClick={() => setInput(q)}
                        className="text-xs shadow-sm"
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
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl p-3.5 ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-muted rounded-bl-md"
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    {msg.role === "assistant" && (
                      <div className="mt-2 space-y-1">
                        {msg.agents_used && msg.agents_used.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {msg.agents_used.map((a) => (
                              <Badge key={a} variant="outline" className="text-xs">
                                {a}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {msg.alerts && msg.alerts.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-destructive">
                            <AlertTriangle className="h-3 w-3" />
                            {msg.alerts.length} alert(s)
                          </div>
                        )}
                        {msg.care_gaps && msg.care_gaps.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                            <Lightbulb className="h-3 w-3" />
                            {msg.care_gaps.length} care gap(s)
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {chatMutation.isPending && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
                <div className="bg-muted rounded-2xl rounded-bl-md p-3.5 flex items-center gap-1.5" data-testid="typing-indicator">
                  <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          <div className="p-4 border-t bg-background/80 backdrop-blur-sm">
            <div className="flex gap-2">
              <Textarea
                placeholder={language === "en" ? "Type your health question..." : "अपना स्वास्थ्य प्रश्न टाइप करें..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                className="min-h-[44px] max-h-32 resize-none rounded-xl"
                data-testid="input-chat"
              />
              <Button
                onClick={sendMessage}
                disabled={!input.trim() || chatMutation.isPending}
                className="h-11 w-11 rounded-xl shrink-0"
                aria-label="Send message"
                data-testid="button-send"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
