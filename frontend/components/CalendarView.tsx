"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { ScreeningData, TheatreData } from "@/lib/api";
import {
  buildCalendarWeeks,
  displayTitle,
  formatAgendaDate,
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
const VISIBLE_COUNT = 5;

function screeningUrl(s: ScreeningData): string {
  const ref = s.raw_source_ref;
  if (!ref) return s.theatre.source_url;
  if (ref.startsWith("/")) {
    try {
      return new URL(ref, new URL(s.theatre.source_url).origin).href;
    } catch {
      return s.theatre.source_url;
    }
  }
  return ref;
}

export function CalendarView({ theatres, screenings, month }: Props) {
  const [selectedSlugs, setSelectedSlugs] = useState<Set<string>>(
    () => new Set(theatres.map((t) => t.slug))
  );
  const [inputValue, setInputValue] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const id = setTimeout(() => setSearchTerm(inputValue.trim()), 250);
    return () => clearTimeout(id);
  }, [inputValue]);

  const selectAll = () => setSelectedSlugs(new Set(theatres.map((t) => t.slug)));

  function toggleSlug(slug: string) {
    setSelectedSlugs((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next.size === 0 ? new Set(theatres.map((t) => t.slug)) : next;
    });
  }

  const filtered = screenings
    .filter((s) => selectedSlugs.size === theatres.length || selectedSlugs.has(s.theatre.slug))
    .filter((s) => !searchTerm || displayTitle(s.movie.title).toLowerCase().includes(searchTerm.toLowerCase()));

  const byDate = filtered.reduce<Record<string, ScreeningData[]>>((acc, s) => {
    const key = screeningDateKey(s.start_time);
    (acc[key] ??= []).push(s);
    return acc;
  }, {});

  for (const key of Object.keys(byDate)) {
    byDate[key].sort((a, b) => a.start_time.localeCompare(b.start_time));
  }

  const [expandedDay, setExpandedDay] = useState<string | null>(null);

  function toggleExpanded(key: string) {
    setExpandedDay((prev) => (prev === key ? null : key));
  }

  const weeks = buildCalendarWeeks(month);
  const [year, m] = month.split("-").map(Number);
  const today = todayKey();

  const monthPrefix = `${String(year)}-${String(m).padStart(2, "0")}`;
  const agendaDates = Object.keys(byDate)
    .filter((k) => k.startsWith(monthPrefix))
    .sort();

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
        <div className="max-w-7xl mx-auto">
          {/* Desktop: pill buttons */}
          <div className="hidden md:flex flex-wrap gap-2">
            <FilterButton
              label="All"
              active={selectedSlugs.size === theatres.length}
              onClick={selectAll}
            />
            {theatres.map((t) => (
              <FilterButton
                key={t.slug}
                label={t.name}
                active={selectedSlugs.has(t.slug)}
                onClick={() => toggleSlug(t.slug)}
              />
            ))}
          </div>
          {/* Mobile: dropdown */}
          <div className="md:hidden">
            <TheatreDropdown
              theatres={theatres}
              selectedSlugs={selectedSlugs}
              onToggle={toggleSlug}
              onSelectAll={selectAll}
            />
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white border-b border-zinc-200 px-4 py-2">
        <div className="max-w-7xl mx-auto">
          <input
            type="search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search screenings…"
            className="w-full sm:w-72 px-3 py-1.5 text-sm rounded-full border border-zinc-200 bg-zinc-50 text-zinc-900 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
          />
        </div>
      </div>

      {/* Desktop: month grid */}
      <main className="hidden md:block max-w-7xl mx-auto px-4 py-4">
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
            const isExpanded = expandedDay === key;
            const visible = dayScreenings.slice(0, VISIBLE_COUNT);
            const hidden = dayScreenings.slice(VISIBLE_COUNT);

            return (
              <div
                key={i}
                className={`min-h-24 p-1.5 ${inMonth ? "bg-white" : "bg-zinc-50"} ${isExpanded ? "ring-1 ring-inset ring-zinc-900" : ""}`}
              >
                {/* Date row — button when day has screenings */}
                {dayScreenings.length > 0 ? (
                  <button
                    onClick={() => toggleExpanded(key)}
                    aria-expanded={isExpanded}
                    className="w-full flex justify-end items-center gap-0.5 mb-1 cursor-pointer"
                  >
                    {isToday ? (
                      <span className="w-6 h-6 bg-zinc-900 text-white rounded-full flex items-center justify-center text-xs font-semibold">
                        {date.getDate()}
                      </span>
                    ) : (
                      <span className={`text-xs font-medium ${inMonth ? "text-zinc-600" : "text-zinc-300"}`}>
                        {date.getDate()}
                      </span>
                    )}
                    <span className={`text-[10px] text-zinc-400 leading-none transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}>
                      ›
                    </span>
                  </button>
                ) : isToday ? (
                  <div className="flex justify-end mb-1">
                    <span className="w-6 h-6 bg-zinc-900 text-white rounded-full flex items-center justify-center text-xs font-semibold">
                      {date.getDate()}
                    </span>
                  </div>
                ) : (
                  <div className={`text-right text-xs font-medium mb-1 ${inMonth ? "text-zinc-600" : "text-zinc-300"}`}>
                    {date.getDate()}
                  </div>
                )}

                {/* Screenings */}
                <div className="space-y-0.5">
                  {(isExpanded ? groupByTheatre(dayScreenings) : groupByTheatre(visible)).map((group) => (
                    <div key={group.name} className="border-t border-zinc-100 pt-0.5 mt-0.5 first:border-t-0 first:pt-0 first:mt-0">
                      <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">
                        {group.name}
                      </div>
                      {group.screenings.map((s) => (
                        <a
                          key={s.id}
                          href={screeningUrl(s)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs leading-snug truncate flex gap-1 hover:bg-zinc-50 rounded"
                          title={`${displayTitle(s.movie.title)} — ${s.theatre.name} — ${formatTime(s.start_time)}`}
                        >
                          <span className="text-zinc-400 tabular-nums shrink-0">
                            {formatTime(s.start_time)}
                          </span>
                          <span className="text-zinc-700 truncate">
                            {displayTitle(s.movie.title)}
                          </span>
                        </a>
                      ))}
                    </div>
                  ))}
                  {!isExpanded && hidden.length > 0 && (
                    <OverflowBadge groups={groupByTheatre(hidden)} />
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

      {/* Mobile: agenda list */}
      <main className="md:hidden max-w-7xl mx-auto px-4 py-4">
        {agendaDates.length === 0 ? (
          <p className="text-center text-zinc-400 text-sm mt-8">
            No screenings found for this month.
          </p>
        ) : (
          <div className="space-y-2">
            {agendaDates.map((key) => {
              const isExpanded = expandedDay === key;
              const count = byDate[key].length;
              return (
                <section key={key}>
                  <button
                    onClick={() => toggleExpanded(key)}
                    aria-expanded={isExpanded}
                    className={`w-full flex items-center justify-between py-1.5 mb-0 pb-1.5 border-b text-left ${
                      key === today ? "border-zinc-900" : "border-zinc-200"
                    }`}
                  >
                    <span className={`text-sm font-semibold ${key === today ? "text-zinc-900" : "text-zinc-500"}`}>
                      {formatAgendaDate(key, today)}
                    </span>
                    <span className="flex items-center gap-1.5 shrink-0">
                      {!isExpanded && (
                        <span className="text-xs text-zinc-400">
                          {count} screening{count !== 1 ? "s" : ""}
                        </span>
                      )}
                      <span className={`text-zinc-400 text-sm leading-none transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}>
                        ›
                      </span>
                    </span>
                  </button>
                  {isExpanded && (
                    <div className="space-y-3 pt-3">
                      {groupByTheatre(byDate[key]).map((group) => (
                        <div key={group.name}>
                          <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium mb-1">
                            {group.name}
                          </div>
                          <div className="space-y-0.5">
                            {group.screenings.map((s) => (
                              <a
                                key={s.id}
                                href={screeningUrl(s)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex gap-3 items-baseline py-1 px-2 -mx-2 rounded active:bg-zinc-100"
                              >
                                <span className="text-xs tabular-nums text-zinc-400 shrink-0 w-16">
                                  {formatTime(s.start_time)}
                                </span>
                                <span className="text-sm text-zinc-800">
                                  {displayTitle(s.movie.title)}
                                </span>
                              </a>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface TheatreGroup {
  name: string;
  screenings: ScreeningData[];
}

function groupByTheatre(screenings: ScreeningData[]): TheatreGroup[] {
  const map = new Map<string, TheatreGroup>();
  for (const s of screenings) {
    if (!map.has(s.theatre.slug)) map.set(s.theatre.slug, { name: s.theatre.name, screenings: [] });
    map.get(s.theatre.slug)!.screenings.push(s);
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
}

// ---------------------------------------------------------------------------

interface OverflowBadgeProps {
  groups: TheatreGroup[];
}

function OverflowBadge({ groups }: OverflowBadgeProps) {
  const totalCount = groups.reduce((sum, g) => sum + g.screenings.length, 0);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [popoverStyle, setPopoverStyle] = useState<React.CSSProperties | null>(null);

  const cancelHide = () => {
    if (hideTimerRef.current !== null) {
      clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  };

  const showPopover = () => {
    cancelHide();
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom - 8;
    const spaceAbove = rect.top - 8;
    const showAbove = spaceAbove > spaceBelow;
    setPopoverStyle(
      showAbove
        ? { position: "fixed", bottom: window.innerHeight - rect.top + 4, left: rect.left, maxHeight: spaceAbove, overflowY: "auto" }
        : { position: "fixed", top: rect.bottom + 4, left: rect.left, maxHeight: spaceBelow, overflowY: "auto" }
    );
  };

  const scheduleHide = () => {
    hideTimerRef.current = setTimeout(() => setPopoverStyle(null), 150);
  };

  return (
    <>
      <button
        ref={triggerRef}
        onMouseEnter={showPopover}
        onMouseLeave={scheduleHide}
        onFocus={showPopover}
        onBlur={scheduleHide}
        aria-expanded={popoverStyle !== null}
        aria-label={`Show ${totalCount} more screenings`}
        className="text-xs text-zinc-400 hover:text-zinc-600 cursor-default focus:outline-none focus-visible:underline"
      >
        +{totalCount} more
      </button>

      {popoverStyle &&
        createPortal(
          <div
            role="list"
            aria-label="Additional screenings"
            style={popoverStyle}
            onMouseEnter={cancelHide}
            onMouseLeave={scheduleHide}
            className="z-50 min-w-52 max-w-72 rounded-lg border border-zinc-200 bg-white py-2 shadow-lg"
          >
            {groups.map((group) => (
              <div key={group.name} className="border-t border-zinc-100 first:border-t-0">
                <div className="px-3 pt-1 pb-0.5 text-[10px] uppercase tracking-wider text-zinc-400 font-medium">
                  {group.name}
                </div>
                {group.screenings.map((s) => (
                  <a
                    key={s.id}
                    role="listitem"
                    href={screeningUrl(s)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-baseline gap-2 px-3 py-0.5 text-xs hover:bg-zinc-50"
                    title={`${displayTitle(s.movie.title)} — ${s.theatre.name}`}
                  >
                    <span className="shrink-0 tabular-nums text-zinc-400">
                      {formatTime(s.start_time)}
                    </span>
                    <span className="truncate text-zinc-700">
                      {displayTitle(s.movie.title)}
                    </span>
                  </a>
                ))}
              </div>
            ))}
          </div>,
          document.body
        )}
    </>
  );
}

// ---------------------------------------------------------------------------

interface TheatreDropdownProps {
  theatres: TheatreData[];
  selectedSlugs: Set<string>;
  onToggle: (slug: string) => void;
  onSelectAll: () => void;
}

function TheatreDropdown({ theatres, selectedSlugs, onToggle, onSelectAll }: TheatreDropdownProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  const allSelected = selectedSlugs.size === theatres.length;

  let label: string;
  if (allSelected) {
    label = "All Theatres";
  } else if (selectedSlugs.size === 1) {
    const slug = [...selectedSlugs][0];
    label = theatres.find((t) => t.slug === slug)?.name ?? "1 Theatre";
  } else {
    label = `${selectedSlugs.size} of ${theatres.length} Theatres`;
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
          !allSelected
            ? "bg-zinc-900 text-white"
            : "bg-zinc-100 text-zinc-600"
        }`}
      >
        {label}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 12 12"
          fill="currentColor"
          className={`w-3 h-3 shrink-0 transition-transform duration-150 ${open ? "rotate-180" : ""}`}
          aria-hidden="true"
        >
          <path d="M6 8.5 1 3.5h10L6 8.5Z" />
        </svg>
      </button>

      {open && (
        <div
          role="listbox"
          aria-multiselectable="true"
          aria-label="Select theatres"
          className="absolute top-full left-0 right-0 mt-1.5 z-50 rounded-xl border border-zinc-200 bg-white shadow-lg overflow-hidden"
        >
          {/* All option */}
          <label className="flex items-center gap-3 px-4 py-3 border-b border-zinc-100 cursor-pointer active:bg-zinc-50">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onSelectAll}
              className="w-4 h-4 accent-zinc-900"
            />
            <span className="text-sm font-medium text-zinc-900">All Theatres</span>
          </label>

          {/* Individual theatres */}
          <div className="max-h-64 overflow-y-auto">
            {theatres.map((t) => (
              <label
                key={t.slug}
                className="flex items-center gap-3 px-4 py-3 border-b border-zinc-50 last:border-b-0 cursor-pointer active:bg-zinc-50"
              >
                <input
                  type="checkbox"
                  checked={selectedSlugs.has(t.slug)}
                  onChange={() => onToggle(t.slug)}
                  className="w-4 h-4 accent-zinc-900 shrink-0"
                />
                <span className="text-sm text-zinc-700">{t.name}</span>
              </label>
            ))}
          </div>

          {/* Done */}
          <div className="px-4 py-3 border-t border-zinc-100">
            <button
              onClick={() => setOpen(false)}
              className="w-full py-2 text-sm font-medium bg-zinc-900 text-white rounded-lg"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

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
