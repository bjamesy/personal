"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import type { RestaurantInterestType, RestaurantResult } from "@/lib/api";

interface Props {
  theatreName: string;
  restaurants: RestaurantResult[];
  interestType: RestaurantInterestType;
  onClickRestaurant: (restaurant: RestaurantResult) => void;
  onDismiss: () => void;
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  return (
    <span className="text-amber-500 text-xs" aria-label={`${rating} stars`}>
      {"★".repeat(full)}
      {half ? "½" : ""}
      <span className="ml-1 text-zinc-600 dark:text-zinc-400 font-normal">{rating.toFixed(1)}</span>
    </span>
  );
}

export function RestaurantRecommendationsModal({
  theatreName,
  restaurants,
  interestType,
  onClickRestaurant,
  onDismiss,
}: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onDismiss();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  const top5 = restaurants.slice(0, 5);

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="recs-modal-title"
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onDismiss}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="relative w-full max-w-sm rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-xl flex flex-col max-h-[80vh]">
        <div className="px-6 pt-6 pb-3 border-b border-zinc-100 dark:border-zinc-800 shrink-0">
          <p
            id="recs-modal-title"
            className="text-sm font-medium text-zinc-900 dark:text-zinc-100 text-center"
          >
            Places to eat near {theatreName}
          </p>
        </div>

        {top5.length === 0 ? (
          <p className="px-6 py-8 text-sm text-zinc-500 dark:text-zinc-400 text-center">
            No restaurants found nearby.
          </p>
        ) : (
          <ul className="overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800">
            {top5.map((r) => (
              <li key={r.name}>
                {r.google_maps_url ? (
                  <a
                    href={r.google_maps_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => onClickRestaurant(r)}
                    className="flex flex-col gap-0.5 px-6 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
                  >
                    <RestaurantRow r={r} />
                  </a>
                ) : (
                  <div className="flex flex-col gap-0.5 px-6 py-3">
                    <RestaurantRow r={r} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

        <div className="px-6 py-4 border-t border-zinc-100 dark:border-zinc-800 shrink-0">
          <button
            onClick={onDismiss}
            className="w-full py-2 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

function RestaurantRow({ r }: { r: RestaurantResult }) {
  return (
    <>
      <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{r.name}</span>
      {r.rating != null && <StarRating rating={r.rating} />}
      {r.address && (
        <span className="text-xs text-zinc-600 dark:text-zinc-400 leading-snug">{r.address}</span>
      )}
      {r.google_maps_url && (
        <span className="text-xs text-blue-600 dark:text-blue-400 mt-0.5">View on Maps →</span>
      )}
    </>
  );
}
