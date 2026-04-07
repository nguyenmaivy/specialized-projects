"use client";

import { useEffect, useMemo, useState } from "react";
import { RefreshCw, ThumbsDown, ThumbsUp, X } from "lucide-react";
import * as api from "@/lib/api";

type Props = {
  open: boolean;
  title: string;
  request: api.ChartInsightRequest | null;
  onClose: () => void;
};

function localeLabel(locale: api.InsightLocale) {
  return locale === "en" ? "EN" : "VI";
}

export default function ChartInsightPanel({ open, title, request, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [insight, setInsight] = useState<api.ChartInsightResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [pollId, setPollId] = useState<string>("");
  const [feedbackSent, setFeedbackSent] = useState<boolean>(false);

  const detailLevel = request?.detailLevel ?? "short";
  const locale = request?.locale ?? "vi";

  const header = useMemo(() => {
    return `${title} · ${detailLevel} · ${localeLabel(locale)}`;
  }, [title, detailLevel, locale]);

  /** Parse basic markdown: **bold**, bullet points, numbered lists */
  function renderMarkdown(text: string) {
    const lines = (text || "").split("\n");
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

  useEffect(() => {
    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;

    const errorDetail = (err: unknown, fallback: string) => {
      if (typeof err !== "object" || err === null) return fallback;
      const anyErr = err as { response?: { data?: { detail?: unknown } } };
      const detail = anyErr.response?.data?.detail;
      return typeof detail === "string" && detail.trim() ? detail : fallback;
    };

    const poll = async (id: string) => {
      try {
        const res = await api.getChartInsight(id);
        if (cancelled) return;
        if (res.status === "processing") {
          pollTimer = setTimeout(() => poll(id), 1200);
          return;
        }
        setInsight(res);
        setLoading(false);
        setPollId("");
      } catch (e: unknown) {
        if (cancelled) return;
        setLoading(false);
        setError(errorDetail(e, "Không thể tải insight."));
      }
    };

    const run = async () => {
      if (!open || !request) return;
      setError("");
      setInsight(null);
      setFeedbackSent(false);
      setLoading(true);
      try {
        const res = await api.fetchChartInsight(request);
        if (cancelled) return;
        if (res.status === "processing") {
          setPollId(res.id);
          pollTimer = setTimeout(() => poll(res.id), 800);
          return;
        }
        setInsight(res);
      } catch (e: unknown) {
        setError(errorDetail(e, "Không thể tạo insight lúc này."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    run();
    return () => {
      cancelled = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [open, request]);

  const sendFeedback = async (useful: boolean) => {
    if (!insight?.id || feedbackSent) return;
    try {
      await api.sendChartInsightFeedback(insight.id, useful);
      setFeedbackSent(true);
    } catch {
      // ignore
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-full sm:w-[520px] bg-white shadow-2xl border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-sm font-semibold text-gray-900 truncate">{header}</div>
            {request?.timeRange ? (
              <div className="text-xs text-gray-500 mt-0.5">
                {request.timeRange.from} → {request.timeRange.to}
              </div>
            ) : null}
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex-1 space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <RefreshCw className="w-4 h-4 animate-spin" />
              {pollId ? "Đang phân tích — sẽ tự cập nhật khi xong..." : "Đang tạo insight..."}
            </div>
          ) : null}

          {error ? (
            <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-sm text-red-700">{error}</div>
          ) : null}

          {insight ? (
            <>
              <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-100 text-sm text-gray-800">
                <div className="space-y-1">{renderMarkdown(insight.summary)}</div>
              </div>

              {insight.highlights?.length ? (
                <div>
                  <div className="text-sm font-semibold text-gray-900 mb-2">Highlights</div>
                  <ul className="space-y-1 text-sm text-gray-700">
                    {insight.highlights.map((h, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-indigo-500 mt-0.5">•</span>
                        <span>{renderMarkdown(h)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {detailLevel === "detailed" && insight.explanations?.length ? (
                <div>
                  <div className="text-sm font-semibold text-gray-900 mb-2">Explanation</div>
                  <div className="space-y-2 text-sm text-gray-700">
                    {insight.explanations.map((e, i) => (
                      <div key={i} className="p-3 rounded-lg border border-gray-200">
                        <div>{renderMarkdown(e.text)}</div>
                        {e.metric_reference ? (
                          <div className="text-xs text-gray-500 mt-1">{e.metric_reference}</div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {insight.actions?.length ? (
                <div>
                  <div className="text-sm font-semibold text-gray-900 mb-2">Suggested actions</div>
                  <ul className="space-y-1 text-sm text-gray-700">
                    {insight.actions.map((a, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-emerald-600 mt-0.5">•</span>
                        <span>{renderMarkdown(a)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div className="pt-2 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
                <div>
                  confidence: <span className="font-medium text-gray-700">{Math.round(insight.confidence * 100)}%</span>
                  {" · "}
                  {insight.cached ? "cache" : "fresh"}
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={feedbackSent}
                    onClick={() => sendFeedback(true)}
                    className="px-2.5 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5"
                    title="Useful"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                    Useful
                  </button>
                  <button
                    disabled={feedbackSent}
                    onClick={() => sendFeedback(false)}
                    className="px-2.5 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1.5"
                    title="Not useful"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                    Not useful
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

