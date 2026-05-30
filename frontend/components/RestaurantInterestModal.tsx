"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import type { RestaurantInterestType } from "@/lib/api";

interface Props {
  theatreName: string;
  onAnswer: (answer: RestaurantInterestType) => void;
  onDismiss: () => void;
}

export function RestaurantInterestModal({ theatreName, onAnswer, onDismiss }: Props) {
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
      aria-labelledby="restaurant-modal-title"
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onDismiss}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="relative w-full max-w-sm rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl p-6 flex flex-col gap-4">
        <p
          id="restaurant-modal-title"
          className="text-sm font-medium text-zinc-900 dark:text-zinc-100 text-center"
        >
          Looking for somewhere to eat near {theatreName}?
        </p>

        <div className="flex flex-col gap-2">
          <button
            onClick={() => onAnswer("before_movie")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 transition-opacity"
          >
            Before the movie
          </button>
          <button
            onClick={() => onAnswer("after_movie")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
          >
            After the movie
          </button>
          <button
            onClick={() => onAnswer("browsing")}
            className="w-full py-2.5 rounded-xl text-sm font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
          >
            Just browsing
          </button>
          <button
            onClick={() => onAnswer("declined")}
            className="w-full py-2.5 rounded-xl text-sm font-medium text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-400 transition-colors"
          >
            No thanks
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
