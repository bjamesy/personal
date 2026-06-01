"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { TheatreData } from "@/lib/api";
import { createCalendarSubscription } from "@/lib/api";

function toWebcalUrl(url: string): string {
  return url.replace(/^https?:\/\//, "webcal://");
}

function isMobileDevice(): boolean {
  return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
}

interface Props {
  theatres: TheatreData[];
  initialSlugs: Set<string>;
  onClose: () => void;
}

export function CalendarSubscribeModal({ theatres, initialSlugs, onClose }: Props) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    () => new Set(theatres.filter((t) => initialSlugs.has(t.slug)).map((t) => t.id))
  );
  const [feedUrl, setFeedUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [copied, setCopied] = useState(false);
  const urlInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  function toggle(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function toggleAll() {
    const enabled = theatres.filter((t) => t.is_cron_enabled);
    const allEnabled = enabled.every((t) => selectedIds.has(t.id));
    setSelectedIds(allEnabled ? new Set() : new Set(enabled.map((t) => t.id)));
  }

  async function handleSubscribe() {
    if (selectedIds.size === 0) return;
    setLoading(true);
    setError(false);
    const result = await createCalendarSubscription(Array.from(selectedIds));
    setLoading(false);
    if (result) {
      setFeedUrl(result.feed_url);
    } else {
      setError(true);
    }
  }

  async function handleCopy() {
    if (!feedUrl) return;
    try {
      await navigator.clipboard.writeText(feedUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      urlInputRef.current?.select();
    }
  }

  const enabledTheatres = theatres.filter((t) => t.is_cron_enabled);
  const allEnabledSelected = enabledTheatres.length > 0 && enabledTheatres.every((t) => selectedIds.has(t.id));

  const modal = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cal-modal-title"
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative z-10 w-full max-w-sm rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-zinc-100 dark:border-zinc-800">
          <h2
            id="cal-modal-title"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            {feedUrl ? "Your calendar feed" : "Subscribe to Calendar"}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-4 h-4">
              <path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z" />
            </svg>
          </button>
        </div>

        {feedUrl ? (
          /* Step 2: open in calendar or copy URL */
          <div className="px-5 py-5 space-y-4">
            {isMobileDevice() ? (
              <>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Tap below to open in your calendar app. It will ask you to confirm the subscription.
                </p>
                <a
                  href={toWebcalUrl(feedUrl)}
                  className="flex items-center justify-center w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-200 transition-colors"
                >
                  Add to Calendar
                </a>
              </>
            ) : (
              <>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  Open in a calendar app, or copy the URL to add it manually.
                </p>
                <a
                  href={toWebcalUrl(feedUrl)}
                  className="flex items-center justify-center w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-200 transition-colors"
                >
                  Open in Calendar
                </a>
              </>
            )}
            <div className="flex gap-2">
              <input
                ref={urlInputRef}
                readOnly
                value={feedUrl}
                onClick={(e) => (e.target as HTMLInputElement).select()}
                className="flex-1 min-w-0 px-3 py-2 text-xs rounded-lg border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-400"
              />
              <button
                onClick={handleCopy}
                className="shrink-0 px-3 py-2 rounded-lg text-xs font-medium border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <button
              onClick={onClose}
              className="w-full py-2 rounded-lg text-xs font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          /* Step 1: theatre selection */
          <>
            <div className="px-5 pt-4 pb-1">
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-3">
                Choose the theatres you want in your feed.
              </p>
              <label className="flex items-center gap-3 py-2 cursor-pointer border-b border-zinc-100 dark:border-zinc-800">
                <input
                  type="checkbox"
                  checked={allEnabledSelected}
                  onChange={toggleAll}
                  className="w-4 h-4 accent-zinc-900 dark:accent-zinc-400"
                />
                <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">All Theatres</span>
              </label>
            </div>

            <div className="max-h-52 overflow-y-auto px-5 pb-2">
              {theatres.map((t) => (
                <label
                  key={t.id}
                  className={`flex items-center gap-3 py-2.5 border-b border-zinc-50 dark:border-zinc-800 last:border-b-0 ${
                    t.is_cron_enabled ? "cursor-pointer" : "cursor-not-allowed opacity-50"
                  }`}
                  title={!t.is_cron_enabled ? "Scraper temporarily unavailable" : undefined}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(t.id)}
                    onChange={() => t.is_cron_enabled && toggle(t.id)}
                    disabled={!t.is_cron_enabled}
                    className="w-4 h-4 accent-zinc-900 dark:accent-zinc-400 shrink-0"
                  />
                  <span className="flex items-center gap-1.5 text-sm text-zinc-700 dark:text-zinc-300">
                    {!t.is_cron_enabled && (
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                    )}
                    {t.name}
                  </span>
                </label>
              ))}
            </div>

            <div className="px-5 py-4 border-t border-zinc-100 dark:border-zinc-800 space-y-2">
              {error && (
                <p className="text-xs text-red-500 dark:text-red-400 text-center">
                  Something went wrong. Please try again.
                </p>
              )}
              <button
                onClick={handleSubscribe}
                disabled={selectedIds.size === 0 || loading}
                className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:bg-zinc-700 dark:hover:bg-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? "Generating…" : "Generate Feed URL"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
