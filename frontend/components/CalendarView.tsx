"use client";

import Link from "next/link";
import { useState } from "react";

import type { ScreeningData, TheatreData } from "@/lib/api";
import {
  buildCalendarWeeks,
  displayTitle,
  formatMonthLabel,
  formatTime,
  nextMonth,
  prevMonth,
  screeningDateKey,
  todayKey,
  toDateKey,
} from "@/lib/utils";

interface Props {
  theatres: TheatreData[];
  screenings: ScreeningData[];
  month: string;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function CalendarView({ theatres, screenings, month }: Props) {
  const [selectedSlug, setSelectedSlug] = useState<string>("all");

  const filtered =
    selectedSlug === "all"
      ? screenings
      : screenings.filter((s) => s.theatre.slug === selectedSlug);

  const byDate = filtered.reduce<Record<string, ScreeningData[]>>((acc, s) => {
    const key = screeningDateKey(s.start_time);
    (acc[key] ??= []).push(s);
    return acc;
  }, {});

  for (const key of Object.keys(byDate)) {
    byDate[key].sort((a, b) => a.start_time.localeCompare(b.start_time));
  }

  const weeks = buildCalendarWeeks(month);
  const [year, m] = month.split("-").map(Number);
  const today = todayKey();

  return (
    <div className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="bg-white border-b border-zinc-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <h1 className="text-lg font-semibold text-zinc-900 tracking-tight">
            Toronto Theatre Screenings
          </h1>
          <div className="flex items-center gap-1">
            <Link
              href={`?month=${prevMonth(month)}`}
              className="px-2 py-1 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded text-lg leading-none"
              aria-label="Previous month"
            >
              ‹
            </Link>
            <span className="w-36 text-center text-sm font-medium text-zinc-700">
              {formatMonthLabel(month)}
            </span>
            <Link
              href={`?month=${nextMonth(month)}`}
              className="px-2 py-1 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded text-lg leading-none"
              aria-label="Next month"
            >
              ›
            </Link>
          </div>
        </div>
      </header>

      {/* Theatre filter */}
      <div className="bg-white border-b border-zinc-200 px-4 py-2">
        <div className="max-w-7xl mx-auto flex flex-wrap gap-2">
          <FilterButton
            label="All"
            active={selectedSlug === "all"}
            onClick={() => setSelectedSlug("all")}
          />
          {theatres.map((t) => (
            <FilterButton
              key={t.slug}
              label={t.name}
              active={selectedSlug === t.slug}
              onClick={() => setSelectedSlug(t.slug)}
            />
          ))}
        </div>
      </div>

      {/* Calendar */}
      <main className="max-w-7xl mx-auto px-4 py-4">
        {/* Day-of-week headers */}
        <div className="grid grid-cols-7 mb-1">
          {DAY_LABELS.map((d) => (
            <div
              key={d}
              className="py-1 text-center text-xs font-medium text-zinc-500 uppercase tracking-wider"
            >
              {d}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="grid grid-cols-7 gap-px bg-zinc-200 rounded-lg overflow-hidden border border-zinc-200">
          {weeks.flat().map((date, i) => {
            const key = toDateKey(date);
            const dayScreenings = byDate[key] ?? [];
            const inMonth =
              date.getMonth() === m - 1 && date.getFullYear() === year;
            const isToday = key === today;

            return (
              <div
                key={i}
                className={`min-h-24 p-1.5 ${inMonth ? "bg-white" : "bg-zinc-50"}`}
              >
                {/* Date number */}
                {isToday ? (
                  <div className="flex justify-end mb-1">
                    <span className="w-6 h-6 bg-zinc-900 text-white rounded-full flex items-center justify-center text-xs font-semibold">
                      {date.getDate()}
                    </span>
                  </div>
                ) : (
                  <div
                    className={`text-right text-xs font-medium mb-1 ${inMonth ? "text-zinc-600" : "text-zinc-300"}`}
                  >
                    {date.getDate()}
                  </div>
                )}

                {/* Screenings */}
                <div className="space-y-0.5">
                  {dayScreenings.slice(0, 5).map((s) => (
                    <div
                      key={s.id}
                      className="text-xs leading-snug truncate"
                      title={`${displayTitle(s.movie.title)} — ${s.theatre.name} — ${formatTime(s.start_time)}`}
                    >
                      <span className="text-zinc-400 tabular-nums">
                        {formatTime(s.start_time)}
                      </span>{" "}
                      <span className="text-zinc-700">
                        {displayTitle(s.movie.title)}
                      </span>
                    </div>
                  ))}
                  {dayScreenings.length > 5 && (
                    <div className="text-xs text-zinc-400">
                      +{dayScreenings.length - 5} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {screenings.length === 0 && (
          <p className="text-center text-zinc-400 text-sm mt-8">
            No screenings found for this month.
          </p>
        )}
      </main>
    </div>
  );
}

function FilterButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
        active
          ? "bg-zinc-900 text-white"
          : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
      }`}
    >
      {label}
    </button>
  );
}
