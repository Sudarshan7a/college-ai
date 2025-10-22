import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Maximize2, Minimize2, X, MessageCircle } from "lucide-react";
import chatIcon from "@/assets/chat-icon.png";

type ChatState = "collapsed" | "normal" | "fullscreen";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export const ChatWidget = () => {
  const [chatState, setChatState] = useState<ChatState>("collapsed");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (chatState !== "collapsed") {
      inputRef.current?.focus();
    }
  }, [chatState]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/ask/quire", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || data.message || "I received your message!",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to send message";
      setError(errorMsg);
      
      // Add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `⚠️ ${errorMsg}. Please make sure the API endpoint is running at http://localhost:8000/ask/quire`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleChatState = () => {
    if (chatState === "collapsed") {
      setChatState("normal");
    } else if (chatState === "normal") {
      setChatState("fullscreen");
    } else {
      setChatState("normal");
    }
  };

  const containerVariants = {
    collapsed: {
      width: "64px",
      height: "64px",
      borderRadius: "32px",
      transition: { duration: 0.3, ease: "easeInOut" as const },
    },
    normal: {
      width: "min(420px, 90vw)",
      height: "min(600px, 80vh)",
      borderRadius: "16px",
      transition: { duration: 0.3, ease: "easeInOut" as const },
    },
    fullscreen: {
      width: "100vw",
      height: "100vh",
      borderRadius: "0px",
      transition: { duration: 0.3, ease: "easeInOut" as const },
    },
  };

  return (
    <>
      <motion.div
        className="fixed z-50 shadow-2xl overflow-hidden"
        style={{
          bottom: chatState === "fullscreen" ? 0 : 24,
          right: chatState === "fullscreen" ? 0 : 24,
          background: chatState === "collapsed" 
            ? "var(--gradient-primary)" 
            : "hsl(var(--card))",
        }}
        initial="collapsed"
        animate={chatState}
        variants={containerVariants}
      >
        {/* Collapsed State - Icon Only */}
        {chatState === "collapsed" && (
          <motion.button
            className="w-full h-full flex items-center justify-center cursor-pointer hover:scale-110 transition-transform"
            onClick={() => setChatState("normal")}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Open chat"
          >
            <img 
              src={chatIcon} 
              alt="Chat" 
              className="w-8 h-8 object-contain"
              onError={(e) => {
                // Fallback if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const fallback = document.createElement('div');
                fallback.innerHTML = '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
                target.parentElement?.appendChild(fallback);
              }}
            />
          </motion.button>
        )}

        {/* Expanded State - Chat Interface */}
        {chatState !== "collapsed" && (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-primary to-accent">
              <div className="flex items-center gap-3">
                <img 
                  src={chatIcon} 
                  alt="Chat" 
                  className="w-8 h-8 object-contain"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>';
                  }}
                />
                <h2 className="text-lg font-semibold text-primary-foreground">Chat Assistant</h2>
              </div>

              <div className="flex items-center gap-2">
                {/* Size Toggle Button */}
                <button
                  onClick={toggleChatState}
                  className="p-2 rounded-lg hover:bg-white/20 transition-colors text-primary-foreground"
                  aria-label={chatState === "normal" ? "Maximize" : "Normal size"}
                >
                  {chatState === "normal" ? (
                    <Maximize2 className="w-5 h-5" />
                  ) : (
                    <Minimize2 className="w-5 h-5" />
                  )}
                </button>

                {/* Close Button */}
                <button
                  onClick={() => setChatState("collapsed")}
                  className="p-2 rounded-lg hover:bg-white/20 transition-colors text-primary-foreground"
                  aria-label="Close chat"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
              <AnimatePresence mode="popLayout">
                {messages.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col items-center justify-center h-full text-center px-4"
                  >
                    <MessageCircle className="w-16 h-16 text-muted-foreground mb-4" />
                    <h3 className="text-xl font-semibold text-foreground mb-2">
                      Welcome to Chat
                    </h3>
                    <p className="text-muted-foreground">
                      Start a conversation by typing a message below
                    </p>
                  </motion.div>
                )}

                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] px-4 py-3 rounded-2xl ${
                        message.role === "user"
                          ? "bg-gradient-to-r from-primary to-accent text-primary-foreground"
                          : "bg-muted text-foreground"
                      }`}
                      style={{
                        boxShadow: message.role === "user" 
                          ? "var(--shadow-elegant)" 
                          : "var(--shadow-soft)",
                      }}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                      <span className={`text-xs mt-1 block ${
                        message.role === "user" 
                          ? "text-primary-foreground/70" 
                          : "text-muted-foreground"
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-start"
                >
                  <div className="bg-muted px-4 py-3 rounded-2xl">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-border bg-card p-4">
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-3 p-2 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive"
                >
                  {error}
                </motion.div>
              )}

              <div className="flex gap-2 items-end">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isLoading}
                  className="flex-1 px-4 py-3 bg-input border border-border rounded-xl text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 transition-all"
                  aria-label="Message input"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="px-4 py-3 bg-gradient-to-r from-primary to-accent text-primary-foreground rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center"
                  style={{ boxShadow: "var(--shadow-elegant)" }}
                  aria-label="Send message"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </>
  );
};
