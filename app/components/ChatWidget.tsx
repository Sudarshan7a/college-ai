"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Maximize2,
  Minimize2,
  X,
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
  Trash2,
  Copy,
  Check,
} from "lucide-react";
import Image from "next/image";
import { LoadingSkeleton } from "./LoadingSkeleton";

type ChatState = "collapsed" | "normal" | "fullscreen";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  query?: string; // Store the query for feedback
  feedback?: "helpful" | "not_helpful" | null;
}

/**
 * ChatWidget Component
 *
 * A floating chat interface with smooth animations.
 * Features three states: collapsed (icon), normal (chat window), fullscreen.
 *
 * Animation Strategy:
 * - Uses Framer Motion variants for declarative state transitions
 * - GPU-accelerated transforms (width, height, borderRadius)
 * - Staggered message animations with AnimatePresence
 * - Smooth spring physics for natural feel
 */
export const ChatWidget = () => {
  const [chatState, setChatState] = useState<ChatState>("collapsed");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "greeting",
      role: "assistant",
      content: "👋 Hello! I'm your College AI Assistant. I can help you with information about:\n\n• 🎓 Admissions & Eligibility\n• 📚 Departments & Programs\n• 💼 Placements & Career\n• 🏫 Campus Facilities\n• 🎉 Events & Activities\n\nWhat would you like to know?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(
    () => `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  );
  const [messageCounter, setMessageCounter] = useState(0);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  // Uses smooth behavior for better UX
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens (accessibility + UX)
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

    const currentMessageIndex = messageCounter;
    setMessageCounter((prev) => prev + 1);

    try {
      // Send to FastAPI backend
      const response = await fetch("http://localhost:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage.content,
          top_k: 3,
          include_sources: false,
          session_id: sessionId,
          message_index: currentMessageIndex,
          message_id: userMessage.id,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "I received your message!",
        timestamp: new Date(),
        query: userMessage.content,
        feedback: null,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Failed to send message";
      setError(errorMsg);

      // Add error message to chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `⚠️ ${errorMsg}. Please make sure the API server is running at http://localhost:8000`,
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

  const handleFeedback = async (
    messageId: string,
    feedbackType: "helpful" | "not_helpful"
  ) => {
    // Update UI optimistically
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === messageId ? { ...msg, feedback: feedbackType } : msg
      )
    );

    try {
      const message = messages.find((m) => m.id === messageId);
      if (!message || !message.query) return;

      const response = await fetch("http://localhost:8000/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_id: messageId,
          helpful: feedbackType === "helpful",
          query: message.query,
          response: message.content,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit feedback");
      }

      // Success - feedback is already updated in UI
      console.log("Feedback submitted successfully");
    } catch (err) {
      console.error("Failed to submit feedback:", err);
      // Revert optimistic update on error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, feedback: null } : msg
        )
      );
    }
  };

  const handleCopy = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error("Failed to copy text:", err);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: "greeting",
        role: "assistant",
        content: "👋 Hello! I'm your College AI Assistant. I can help you with information about:\n\n• 🎓 Admissions & Eligibility\n• 📚 Departments & Programs\n• 💼 Placements & Career\n• 🏫 Campus Facilities\n• 🎉 Events & Activities\n\nWhat would you like to know?",
        timestamp: new Date(),
      },
    ]);
    setInputValue("");
    setError(null);
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

  /**
   * Animation Variants
   *
   * Uses easeInOut for smooth, natural transitions.
   * Width/height changes are GPU-accelerated.
   * BorderRadius morphs create elegant state changes.
   */
  const containerVariants = {
    collapsed: {
      width: "64px",
      height: "64px",
      borderRadius: "32px",
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1], // Custom cubic-bezier for buttery-smooth
      },
    },
    normal: {
      width: "min(420px, 90vw)",
      height: "min(600px, 80vh)",
      borderRadius: "16px",
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
        // Stagger width and height slightly for more natural feel
        width: { duration: 0.3 },
        height: { duration: 0.3, delay: 0.05 },
      },
    },
    fullscreen: {
      width: "100vw",
      height: "100vh",
      borderRadius: "0px",
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      },
    },
  };

  /**
   * Message Animation Variants
   *
   * Slide-up with fade creates polished message appearance.
   * Exit animations prevent layout shift.
   */
  const messageVariants = {
    initial: {
      opacity: 0,
      y: 20,
      scale: 0.95,
    },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.2,
        ease: "easeOut",
      },
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: {
        duration: 0.15,
      },
    },
  };

  return (
    <>
      <motion.div
        className="fixed z-50 shadow-2xl overflow-hidden"
        style={{
          bottom: chatState === "fullscreen" ? 0 : 24,
          right: chatState === "fullscreen" ? 0 : 24,
          background:
            chatState === "collapsed"
              ? "linear-gradient(135deg, hsl(262 83% 58%), hsl(217 91% 60%))"
              : "hsl(var(--card))",
        }}
        initial="collapsed"
        animate={chatState}
        //ignore ts error below
        // @ts-excpect-error @ts-ignore
        variants={containerVariants}
      >
        {/* Collapsed State - Icon Only */}
        {chatState === "collapsed" && (
          <motion.button
            className="w-full h-full flex items-center justify-center cursor-pointer"
            onClick={() => setChatState("normal")}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            aria-label="Open chat"
          >
            <MessageCircle className="w-8 h-8 text-white" />
          </motion.button>
        )}

        {/* Expanded State - Chat Interface */}
        {chatState !== "collapsed" && (
          <div className="flex flex-col h-full">
            {/* Header with Logo */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-[hsl(262_83%_58%)] to-[hsl(217_91%_60%)]">
              <div className="flex items-center gap-3">
                <Image
                  src="/logo.png"
                  alt="College Logo"
                  width={40}
                  height={40}
                  className="rounded-lg"
                />
                <div>
                  <h2 className="text-lg font-semibold text-white leading-tight">
                    College AI Assistant
                  </h2>
                  <p className="text-xs text-white/70">Ask me anything</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Clear Chat Button */}
                <button
                  onClick={handleClearChat}
                  className="p-2 rounded-lg hover:bg-white/20 transition-colors text-white"
                  aria-label="Clear chat"
                  title="Clear conversation"
                >
                  <Trash2 className="w-5 h-5" />
                </button>

                {/* Size Toggle Button */}
                <button
                  onClick={toggleChatState}
                  className="p-2 rounded-lg hover:bg-white/20 transition-colors text-white"
                  aria-label={
                    chatState === "normal" ? "Maximize" : "Normal size"
                  }
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
                  className="p-2 rounded-lg hover:bg-white/20 transition-colors text-white"
                  aria-label="Close chat"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
              <AnimatePresence mode="popLayout">

                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    variants={messageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div className="flex flex-col gap-2 max-w-[80%]">
                      <div
                        className={`px-4 py-3 rounded-2xl ${
                          message.role === "user"
                            ? "bg-gradient-to-r from-[hsl(262_83%_58%)] to-[hsl(217_91%_60%)] text-white"
                            : "bg-muted text-foreground"
                        }`}
                        style={{
                          boxShadow:
                            message.role === "user"
                              ? "0 10px 40px -10px hsl(262 83% 58% / 0.2)"
                              : "0 4px 20px -2px hsl(240 10% 15% / 0.1)",
                        }}
                      >
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                        <span
                          className={`text-xs mt-1 block ${
                            message.role === "user"
                              ? "text-white/70"
                              : "text-muted-foreground"
                          }`}
                        >
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>

                      {/* Feedback buttons for assistant messages */}
                      {message.role === "assistant" && (
                        <div className="flex gap-2 ml-1">
                          <button
                            onClick={() =>
                              handleFeedback(message.id, "helpful")
                            }
                            className={`p-1.5 rounded-lg transition-all hover:bg-muted ${
                              message.feedback === "helpful"
                                ? "bg-green-100 dark:bg-green-900/30"
                                : "hover:scale-110"
                            }`}
                            title="Helpful"
                            aria-label="Mark as helpful"
                          >
                            <ThumbsUp
                              className={`w-4 h-4 ${
                                message.feedback === "helpful"
                                  ? "fill-green-600 text-green-600 dark:fill-green-400 dark:text-green-400"
                                  : "text-muted-foreground"
                              }`}
                            />
                          </button>
                          <button
                            onClick={() =>
                              handleFeedback(message.id, "not_helpful")
                            }
                            className={`p-1.5 rounded-lg transition-all hover:bg-muted ${
                              message.feedback === "not_helpful"
                                ? "bg-red-100 dark:bg-red-900/30"
                                : "hover:scale-110"
                            }`}
                            title="Not helpful"
                            aria-label="Mark as not helpful"
                          >
                            <ThumbsDown
                              className={`w-4 h-4 ${
                                message.feedback === "not_helpful"
                                  ? "fill-red-600 text-red-600 dark:fill-red-400 dark:text-red-400"
                                  : "text-muted-foreground"
                              }`}
                            />
                          </button>
                          <div className="w-px h-4 bg-border my-auto mx-1" />
                          <button
                            onClick={() => handleCopy(message.content, message.id)}
                            className="p-1.5 rounded-lg transition-all hover:bg-muted hover:scale-110"
                            title="Copy to clipboard"
                            aria-label="Copy message"
                          >
                            {copiedId === message.id ? (
                              <Check className="w-4 h-4 text-green-500" />
                            ) : (
                              <Copy className="w-4 h-4 text-muted-foreground" />
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Loading Indicator - Animated Dots */}
              {isLoading && <LoadingSkeleton />}

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
                  className="px-4 py-3 bg-gradient-to-r from-[hsl(262_83%_58%)] to-[hsl(217_91%_60%)] text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-lg"
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
