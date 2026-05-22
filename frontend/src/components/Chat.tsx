"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "ai";
  content: string;
  code?: string;
  language?: string;
  strategyId?: string;
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      role: "ai",
      content: "🤖 Welcome to AI Strategy Builder!\n\nDescribe your trading strategy in English, and I'll generate fully deployable Python code. Examples:\n\n• 'Buy when RSI goes below 30, sell when it goes above 70'\n• 'MACD strategy with fast line 12, slow line 26'\n• 'Buy when 10-day SMA crosses above 30-day SMA'\n• 'Time-based strategy: buy at 9:15 AM, sell at 3:00 PM'\n\nWhat strategy would you like to build?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [codeMode, setCodeMode] = useState<"full" | "template">("full");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function handleSendMessage() {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const endpoint = codeMode === "full" ? "/api/strategies/generate-code" : "/api/strategies/parse";
      
      const res = await api<{
        strategy: { id: string };
        code?: string;
        config?: Record<string, unknown>;
        language?: string;
        ai_source: string;
      }>(endpoint, {
        method: "POST",
        body: JSON.stringify({
          english: input,
          name: `Strategy ${new Date().toLocaleTimeString()}`,
        }),
      });

      let aiMessage: Message;

      if (codeMode === "full" && res.code) {
        aiMessage = {
          id: Date.now().toString(),
          role: "ai",
          content: `✅ Generated full Python trading strategy! The code is ready to deploy.\n\nKey features:\n• Complete strategy class with indicators\n• Buy/Sell signal generation\n• Backtesting execution\n• P&L tracking\n\nYou can now:\n1. Review the code\n2. Click "View Code" to see implementation details\n3. Deploy to Railway workers\n4. Run backtests`,
          code: res.code,
          language: "python",
          strategyId: res.strategy.id,
        };
      } else if (res.config) {
        aiMessage = {
          id: Date.now().toString(),
          role: "ai",
          content: `✅ Strategy template created! This uses a predefined safe template (${
            (res.config as any).strategy_type || "RSI"
          }).\n\nYou can:\n1. Review the configuration\n2. Run unlimited backtests\n3. Deploy to live simulation\n4. Switch to full code mode for more control`,
          code: JSON.stringify(res.config, null, 2),
          language: "json",
          strategyId: res.strategy.id,
        };
      }

      setMessages((prev) => [...prev, aiMessage!]);
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "ai",
        content: `❌ Error: ${error instanceof Error ? error.message : "Failed to generate strategy"}.\n\nTips:\n• Use clear trading terminology\n• Specify indicators (RSI, MACD, SMA, etc.)\n• Include entry and exit conditions\n• Try again with more details`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyPress(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  function copyCode(code: string) {
    navigator.clipboard.writeText(code);
    alert("Code copied to clipboard!");
  }

  return (
    <div className="fixed inset-0 flex flex-col bg-gradient-to-br from-slate-900 via-surface to-slate-900">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-slate-700 bg-slate-800/50 backdrop-blur p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              🤖 AI Strategy Builder
            </h1>
            <p className="text-xs text-slate-500">Generates full production-ready Python code</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCodeMode("full")}
              className={`px-3 py-1 text-xs rounded-lg font-semibold transition ${
                codeMode === "full"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              🐍 Full Code
            </button>
            <button
              onClick={() => setCodeMode("template")}
              className={`px-3 py-1 text-xs rounded-lg font-semibold transition ${
                codeMode === "template"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}
            >
              📋 Template
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg"
                  : "bg-slate-800/80 text-slate-100 border border-slate-700"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>

              {msg.code && (
                <div className="mt-4 bg-black/50 rounded-lg overflow-hidden border border-slate-600">
                  <div className="bg-slate-900 px-4 py-3 text-xs text-slate-400 font-mono flex justify-between items-center">
                    <span>📝 {msg.language?.toUpperCase()}</span>
                    <div className="flex gap-2">
                      {msg.strategyId && (
                        <a
                          href={`/backtest/${msg.strategyId}`}
                          className="text-emerald-400 hover:text-emerald-300 underline text-xs"
                        >
                          📊 Backtest
                        </a>
                      )}
                      <button
                        onClick={() => copyCode(msg.code!)}
                        className="text-blue-400 hover:text-blue-300 underline text-xs"
                      >
                        📋 Copy
                      </button>
                    </div>
                  </div>
                  <pre className="p-4 text-xs text-emerald-300 font-mono overflow-x-auto max-h-96">
                    {msg.code.length > 2000 ? msg.code.substring(0, 2000) + "\n... (truncated)" : msg.code}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800/80 text-slate-100 border border-slate-700 rounded-lg px-4 py-3">
              <div className="flex gap-3 items-center">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full pulse-dot"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full pulse-dot" style={{ animationDelay: "0.2s" }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full pulse-dot" style={{ animationDelay: "0.4s" }}></div>
                </div>
                <span className="text-sm text-slate-400">
                  {codeMode === "full" ? "Generating Python code..." : "Creating strategy template..."}
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-slate-700 bg-slate-800/50 backdrop-blur p-4">
        <div className="flex gap-2 mb-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              codeMode === "full"
                ? "Describe your trading strategy... (generates full Python code)"
                : "Describe your trading strategy... (uses safe templates)"
            }
            className="input flex-1 resize-none max-h-32 bg-slate-900 border-slate-600 placeholder-slate-500"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={handleSendMessage}
            disabled={loading || !input.trim()}
            className="btn-primary self-end h-fit px-6 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600"
          >
            {loading ? "⏳" : "✉️"}
          </button>
        </div>
        <p className="text-xs text-slate-500 text-center">Press Enter to send • Shift+Enter for new line</p>
      </div>
    </div>
  );
}
