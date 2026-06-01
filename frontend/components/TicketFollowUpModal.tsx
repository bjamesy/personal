"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import type { TicketConfirmedStatus } from "@/lib/api";

interface Props {
  movieTitle?: string;
  onAnswer: (answer: TicketConfirmedStatus) => void;
  onDismiss: () => void;
}

export function TicketFollowUpModal({ movieTitle, onAnswer, onDismiss }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onDismiss();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ticket-modal-title"
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onDismiss}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={ref}
        className="relative w-full max-w-sm rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl p-6 flex flex-col gap-4"
      >
        <p
          id="ticket-modal-title"
          className="text-sm font-medium text-zinc-900 dark:text-zinc-100 text-center"
        >
          Did you end up getting tickets
          {movieTitle ? (
            <> for <span className="italic">{movieTitle}</span>?</>
          ) : "?"}
        </p>

        <div className="flex flex-col gap-2">
          <button
            onClick={() => onAnswer("yes")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity"
          >
            Yes
          </button>
          <button
            onClick={() => onAnswer("no")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
          >
            No
          </button>
          <button
            onClick={() => onAnswer("not_yet")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
          >
            Not yet
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
