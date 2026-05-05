"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import * as api from "@/lib/api";
import { AlertTriangle, Bot, Lightbulb, MessageSquare, RefreshCw, Send, Sparkles } from "lucide-react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  followups?: string[];
};

interface InsightsAssistantProps {
  filters: api.Filters;
  refreshKey: number;
}

function toBullets(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => (line.startsWith("-") ? line.slice(1).trim() : line));
}

/** Parse basic markdown: **bold**, bullet points, numbered lists */
function renderMarkdown(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) return <br key={i} />;

    // Parse inline **bold**
    const parts = trimmed.split(/(\*\*[^*]+\*\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={j} className="font-semibold text-indigo-700">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

    // Bullet point
    if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      return (
        <div key={i} className="flex gap-1.5 ml-1">
          <span className="text-indigo-400 mt-0.5">•</span>
          <span>{rendered.map((r, idx) => (typeof r === "string" ? r.replace(/^[-•]\s*/, "") : r))}</span>
        </div>
      );
    }

    // Numbered list
    const numMatch = trimmed.match(/^(\d+)\.\s/);
    if (numMatch) {
      return (
        <div key={i} className="flex gap-1.5 ml-1">
          <span className="text-indigo-400 font-medium min-w-[1.2em]">{numMatch[1]}.</span>
          <span>{rendered.map((r, idx) => (typeof r === "string" ? r.replace(/^\d+\.\s*/, "") : r))}</span>
        </div>
      );
    }

    return <p key={i}>{rendered}</p>;
  });
}

export default function InsightsAssistant({ filters, refreshKey }: InsightsAssistantProps) {
  const [activeTab, setActiveTab] = useState<"insights" | "chat">("insights");
  const [isLoading, setIsLoading] = useState(false);
  const [analysisRunId, setAnalysisRunId] = useState<string>("");
  const [summary, setSummary] = useState("");
  const [widgets, setWidgets] = useState<api.AIInsightWidget[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const filtersKey = useMemo(() => JSON.stringify(filters), [filters]);

  // Auto-scroll to latest message
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      const parsedFilters = JSON.parse(filtersKey) as api.Filters;
      if (!parsedFilters.start_date || !parsedFilters.end_date || refreshKey <= 0) return;
      setIsLoading(true);
      setChatMessages([]);
      try {
        const analysis = await api.runAnalysis(parsedFilters);
        if (cancelled) return;
        setAnalysisRunId(analysis.analysis_run_id);

        const insights = await api.fetchAIInsights(analysis.analysis_run_id);
        if (cancelled) return;
        setSummary(insights.executive_summary_markdown);
        setWidgets(insights.widgets || []);
        setPrompts(insights.suggested_prompts || []);
      } catch (error) {
        console.error(error);
        if (!cancelled) {
          setSummary("Không thể tải AI insights cho bộ lọc hiện tại.");
          setWidgets([]);
          setPrompts([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    run();
    return () => {
      cancelled = true;
    };
  }, [filtersKey, refreshKey]);

  const groupedWidgets = useMemo(() => {
    return {
      insight: widgets.filter((w) => w.widget_type === "insight"),
      risk: widgets.filter((w) => w.widget_type === "risk"),
      what_if: widgets.filter((w) => w.widget_type === "what_if"),
    };
  }, [widgets]);

  const sendMessage = async (value?: string) => {
    const message = (value ?? chatInput).trim();
    if (!message || !analysisRunId) return;
    setIsSending(true);
    setChatMessages((prev) => [...prev, { role: "user", content: message }]);
    setChatInput("");
    try {
      const response = await api.sendAIChat(analysisRunId, message);
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer_markdown,
          followups: response.followups || [],
        },
      ]);
    } catch (error) {
      console.error(error);
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Không thể trả lời lúc này. Vui lòng thử lại sau." },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const iconForType = (type: api.AIInsightWidget["widget_type"]) => {
    if (type === "risk") return <AlertTriangle className="w-4 h-4 text-amber-600" />;
    if (type === "what_if") return <Sparkles className="w-4 h-4 text-violet-600" />;
    return <Lightbulb className="w-4 h-4 text-blue-600" />;
  };

  const defaultPrompts = [
    "Đánh giá hiệu suất kinh doanh hiện tại",
    "Category nào có doanh thu cao nhất?",
    "Rủi ro lớn nhất trong giai đoạn này là gì?",
    "So sánh doanh thu giữa các region",
  ];

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 h-fit sticky top-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-gray-800">AI Insights Assistant</h3>
        </div>
        {isLoading && <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />}
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab("insights")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${activeTab === "insights" ? "bg-indigo-50 text-indigo-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
        >
          Insights
        </button>
        <button
          onClick={() => setActiveTab("chat")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${activeTab === "chat" ? "bg-indigo-50 text-indigo-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
        >
          Chat
        </button>
      </div>

      {activeTab === "insights" ? (
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-100 text-sm text-gray-700">
            {summary ? <div className="space-y-1">{renderMarkdown(summary)}</div> : "Insights sẽ xuất hiện sau khi tải dữ liệu."}
          </div>

          {[...groupedWidgets.insight, ...groupedWidgets.risk, ...groupedWidgets.what_if].map((widget, idx) => (
            <div key={`${widget.title}-${idx}`} className="p-3 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                {iconForType(widget.widget_type)}
                <p className="font-medium text-sm text-gray-800">{widget.title}</p>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                {renderMarkdown(widget.content_markdown)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="max-h-96 overflow-y-auto space-y-3 pr-1">
            {chatMessages.length === 0 ? (
              <div className="text-sm text-gray-500 p-3 rounded-lg bg-gray-50">
                <p className="mb-2 font-medium">Thử hỏi:</p>
                <div className="space-y-1.5">
                  {(prompts.length ? prompts : defaultPrompts).map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(p)}
                      className="block text-left text-indigo-700 hover:text-indigo-900 hover:underline text-sm transition-colors"
                    >
                      <MessageSquare className="inline w-3 h-3 mr-1.5" />
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              chatMessages.map((msg, idx) => (
                <div key={idx}>
                  <div
                    className={`p-3 rounded-lg text-sm leading-relaxed ${
                      msg.role === "user"
                        ? "bg-indigo-600 text-white ml-6"
                        : "bg-gray-100 text-gray-700 mr-6"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="space-y-1">{renderMarkdown(msg.content)}</div>
                    ) : (
                      msg.content
                    )}
                  </div>
                  {/* Followup suggestions after assistant messages */}
                  {msg.role === "assistant" && msg.followups && msg.followups.length > 0 && (
                    <div className="mt-2 mr-6 flex flex-wrap gap-1.5">
                      {msg.followups.map((followup, fIdx) => (
                        <button
                          key={fIdx}
                          onClick={() => sendMessage(followup)}
                          disabled={isSending}
                          className="text-xs px-2.5 py-1 rounded-full border border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors disabled:opacity-50 text-left"
                        >
                          {followup}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
            {isSending && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-gray-100 mr-6 text-sm text-gray-500">
                <RefreshCw className="w-3 h-3 animate-spin" />
                Đang phân tích...
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="flex gap-2">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) sendMessage();
              }}
              placeholder="Hỏi về doanh thu, rủi ro, đánh giá..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow"
            />
            <button
              onClick={() => sendMessage()}
              disabled={isSending || !analysisRunId}
              className="px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
