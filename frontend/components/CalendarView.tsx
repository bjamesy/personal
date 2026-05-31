"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { RestaurantInterestType, RestaurantResult, ScreeningAttributeData, ScreeningData, TheatreData, TicketConfirmedStatus } from "@/lib/api";
import { fetchRestaurants, patchOutboundClick, recordOutboundClick, recordRecommendationClick, recordRestaurantInterest } from "@/lib/api";
import { CalendarSubscribeModal } from "@/components/CalendarSubscribeModal";
import { RestaurantInterestModal } from "@/components/RestaurantInterestModal";
import { RestaurantRecommendationsModal } from "@/components/RestaurantRecommendationsModal";
import { TicketFollowUpModal } from "@/components/TicketFollowUpModal";
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
const PENDING_CLICK_KEY = "pending_outbound_click";

interface PendingClick {
  id: string | null; // null while the API call is in-flight
  screeningId: string;
  theatreId: string;
  theatreName: string;
  shownAt?: number;
}

interface RestaurantModalState {
  clickId: string;
  screeningId: string;
  theatreId: string;
  theatreName: string;
}

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
  const [selectedAttributeSlugs, setSelectedAttributeSlugs] = useState<Set<string>>(new Set());
  const [inputValue, setInputValue] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [modalClickId, setModalClickId] = useState<string | null>(null);
  const [restaurantModal, setRestaurantModal] = useState<RestaurantModalState | null>(null);
  const [restaurantLoading, setRestaurantLoading] = useState(false);
  const [recommendationsModal, setRecommendationsModal] = useState<{
    restaurants: RestaurantResult[];
    screeningId: string;
    outboundClickId: string;
    theatreId: string;
    theatreName: string;
    interestType: RestaurantInterestType;
  } | null>(null);
  const [calendarSubscribeOpen, setCalendarSubscribeOpen] = useState(false);
  const modalTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingTheatreRef = useRef<{ screeningId: string; theatreId: string; theatreName: string } | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setSearchTerm(inputValue.trim()), 250);
    return () => clearTimeout(id);
  }, [inputValue]);

  // When the user returns to this tab, check for a pending outbound click and
  // show the follow-up modal after a 5-second delay (once per click).
  useEffect(() => {
    function maybeShowModal() {
      if (document.visibilityState !== "visible") return;
      try {
        const raw = localStorage.getItem(PENDING_CLICK_KEY);
        if (!raw) return;
        const pending: PendingClick = JSON.parse(raw);
        if (pending.shownAt) return; // already shown this session

        if (!pending.id) {
          // API call still in-flight; retry shortly
          modalTimerRef.current = setTimeout(maybeShowModal, 500);
          return;
        }

        modalTimerRef.current = setTimeout(() => {
          // Mark as shown so we don't re-trigger on another visibility change
          const updated: PendingClick = { ...pending, shownAt: Date.now() };
          localStorage.setItem(PENDING_CLICK_KEY, JSON.stringify(updated));
          setModalClickId(pending.id!);
          // Stash theatre info in a ref so handleModalAnswer can access it
          pendingTheatreRef.current = { screeningId: pending.screeningId, theatreId: pending.theatreId, theatreName: pending.theatreName };
        }, 5000);
      } catch {
        localStorage.removeItem(PENDING_CLICK_KEY);
      }
    }

    document.addEventListener("visibilitychange", maybeShowModal);
    return () => {
      document.removeEventListener("visibilitychange", maybeShowModal);
      if (modalTimerRef.current !== null) clearTimeout(modalTimerRef.current);
    };
  }, []);

  async function handleScreeningClick(
    e: React.MouseEvent<HTMLAnchorElement>,
    s: ScreeningData
  ) {
    // Write a placeholder immediately so visibilitychange fires before the
    // API responds still has something to detect.
    try {
      const placeholder: PendingClick = { id: null, screeningId: s.id, theatreId: s.theatre.id, theatreName: s.theatre.name };
      localStorage.setItem(PENDING_CLICK_KEY, JSON.stringify(placeholder));
    } catch {}

    const click = await recordOutboundClick(s.id);
    if (click) {
      try {
        const pending: PendingClick = { id: click.id, screeningId: s.id, theatreId: s.theatre.id, theatreName: s.theatre.name };
        localStorage.setItem(PENDING_CLICK_KEY, JSON.stringify(pending));
      } catch {}
    } else {
      localStorage.removeItem(PENDING_CLICK_KEY);
    }
  }

  async function handleModalAnswer(answer: TicketConfirmedStatus) {
    const id = modalClickId;
    const theatre = pendingTheatreRef.current;
    setModalClickId(null);
    localStorage.removeItem(PENDING_CLICK_KEY);
    if (id) {
      await patchOutboundClick(id, {
        ticket_confirmed: answer,
        prompted_at: new Date().toISOString(),
      });
    }
    if (answer === "yes" && id && theatre) {
      setRestaurantModal({ clickId: id, screeningId: theatre.screeningId, theatreId: theatre.theatreId, theatreName: theatre.theatreName });
    }
  }

  function handleModalDismiss() {
    const id = modalClickId;
    setModalClickId(null);
    localStorage.removeItem(PENDING_CLICK_KEY);
    if (id) {
      patchOutboundClick(id, { prompted_at: new Date().toISOString() });
    }
  }

  async function handleRestaurantAnswer(answer: RestaurantInterestType) {
    const state = restaurantModal;
    setRestaurantModal(null);
    if (!state) return;

    await recordRestaurantInterest(state.clickId, answer);

    if (answer === "declined") return;

    setRestaurantLoading(true);
    const restaurants = await fetchRestaurants(state.theatreId, answer);
    setRestaurantLoading(false);
    setRecommendationsModal({
      restaurants,
      screeningId: state.screeningId,
      outboundClickId: state.clickId,
      theatreId: state.theatreId,
      theatreName: state.theatreName,
      interestType: answer,
    });
  }

  function handleRestaurantDismiss() {
    setRestaurantModal(null);
  }

  async function handleRecommendationClick(restaurant: RestaurantResult) {
    if (!recommendationsModal) return;
    await recordRecommendationClick(
      recommendationsModal.screeningId,
      recommendationsModal.outboundClickId,
      restaurant.name,
      recommendationsModal.interestType,
      restaurant.place_id,
      restaurant.place_metadata
    );
  }

  const allSelected = selectedSlugs.size === theatres.length;

  function selectAll() {
    setSelectedSlugs(
      allSelected ? new Set() : new Set(theatres.map((t) => t.slug))
    );
  }

  function toggleSlug(slug: string) {
    setSelectedSlugs((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next;
    });
  }

  function toggleAttributeSlug(slug: string) {
    setSelectedAttributeSlugs((prev) => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next;
    });
  }

  // Derive available attributes grouped by category from the full screenings list.
  const attributesByCategory = screenings.reduce<Map<string, ScreeningAttributeData[]>>((acc, s) => {
    for (const attr of s.attributes) {
      if (!acc.has(attr.category)) acc.set(attr.category, []);
      const existing = acc.get(attr.category)!;
      if (!existing.some((a) => a.slug === attr.slug)) existing.push(attr);
    }
    return acc;
  }, new Map());

  const filtered = screenings
    .filter((s) => allSelected || selectedSlugs.has(s.theatre.slug))
    .filter((s) => !searchTerm || displayTitle(s.movie.title).toLowerCase().includes(searchTerm.toLowerCase()))
    .filter((s) => selectedAttributeSlugs.size === 0 || s.attributes.some((a) => selectedAttributeSlugs.has(a.slug)));

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
    <div className="min-h-screen relative">
      {/* Background image */}
      <div className="fixed inset-0 -z-10">
        <Image
          src="/llewyn.webp"
          alt=""
          fill
          priority
          className="object-cover object-center"
        />
        <div className="absolute inset-0 bg-white/55 dark:bg-zinc-950/65" />
      </div>
      {/* Header */}
      <header className="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-sm border-b border-zinc-200/60 dark:border-zinc-800/60 px-4 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
            Toronto Theatre Screenings
          </h1>
          <div className="flex items-center gap-1">
            <Link
              href={`?month=${prevMonth(month)}`}
              className="px-2 py-1 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded text-lg leading-none"
              aria-label="Previous month"
            >
              ‹
            </Link>
            <span className="w-36 text-center text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {formatMonthLabel(month)}
            </span>
            <Link
              href={`?month=${nextMonth(month)}`}
              className="px-2 py-1 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded text-lg leading-none"
              aria-label="Next month"
            >
              ›
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Theatre filter */}
      <div className="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-sm border-b border-zinc-200/60 dark:border-zinc-800/60 px-4 py-2.5">
        <div className="max-w-7xl mx-auto">
          {/* Desktop: pill buttons + subscribe */}
          <div className="hidden md:flex flex-wrap items-center gap-2 py-0.5">
            <FilterButton
              label="All"
              active={allSelected}
              onClick={selectAll}
            />
            {theatres.map((t) => (
              <FilterButton
                key={t.slug}
                label={t.name}
                active={selectedSlugs.has(t.slug)}
                disabled={!t.is_cron_enabled}
                onClick={() => toggleSlug(t.slug)}
              />
            ))}
            <button
              onClick={() => setCalendarSubscribeOpen(true)}
              className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              aria-label="Subscribe to Calendar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5 shrink-0" aria-hidden="true">
                <path fillRule="evenodd" d="M4 1.75a.75.75 0 0 1 1.5 0V3h5V1.75a.75.75 0 0 1 1.5 0V3h.25A2.75 2.75 0 0 1 15 5.75v7.5A2.75 2.75 0 0 1 12.25 16H3.75A2.75 2.75 0 0 1 1 13.25v-7.5A2.75 2.75 0 0 1 3.75 3H4V1.75ZM3.75 4.5c-.69 0-1.25.56-1.25 1.25V6.5h11V5.75c0-.69-.56-1.25-1.25-1.25H3.75ZM2.5 8v5.25c0 .69.56 1.25 1.25 1.25h8.5c.69 0 1.25-.56 1.25-1.25V8h-11Z" clipRule="evenodd" />
              </svg>
              Subscribe
            </button>
          </div>
          {/* Mobile: dropdown + subscribe */}
          <div className="md:hidden flex items-center gap-2">
            <TheatreDropdown
              theatres={theatres}
              selectedSlugs={selectedSlugs}
              onToggle={toggleSlug}
              onSelectAll={selectAll}
            />
            <button
              onClick={() => setCalendarSubscribeOpen(true)}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors shrink-0"
              aria-label="Subscribe to Calendar"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3.5 h-3.5 shrink-0" aria-hidden="true">
                <path fillRule="evenodd" d="M4 1.75a.75.75 0 0 1 1.5 0V3h5V1.75a.75.75 0 0 1 1.5 0V3h.25A2.75 2.75 0 0 1 15 5.75v7.5A2.75 2.75 0 0 1 12.25 16H3.75A2.75 2.75 0 0 1 1 13.25v-7.5A2.75 2.75 0 0 1 3.75 3H4V1.75ZM3.75 4.5c-.69 0-1.25.56-1.25 1.25V6.5h11V5.75c0-.69-.56-1.25-1.25-1.25H3.75ZM2.5 8v5.25c0 .69.56 1.25 1.25 1.25h8.5c.69 0 1.25-.56 1.25-1.25V8h-11Z" clipRule="evenodd" />
              </svg>
              Subscribe
            </button>
          </div>
        </div>
      </div>

      {/* Attribute filters */}
      {attributesByCategory.size > 0 && (
        <div className="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-sm border-b border-zinc-200/60 dark:border-zinc-800/60 px-4 py-2.5">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-x-4 gap-y-2">
            {[...attributesByCategory.entries()].map(([category, attrs]) => (
              <div key={category} className="flex items-center gap-1.5">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400 shrink-0">
                  {category}
                </span>
                {attrs.map((attr) => (
                  <FilterButton
                    key={attr.slug}
                    label={attr.label}
                    active={selectedAttributeSlugs.has(attr.slug)}
                    onClick={() => toggleAttributeSlug(attr.slug)}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-sm border-b border-zinc-200/60 dark:border-zinc-800/60 px-4 py-2.5">
        <div className="max-w-7xl mx-auto">
          <input
            type="search"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search screenings…"
            className="w-full sm:w-72 px-3 py-1.5 text-sm rounded-full border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-400 focus:border-transparent"
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
              className="py-1.5 text-center text-[11px] font-medium text-zinc-600 dark:text-zinc-500 uppercase tracking-wider"
            >
              {d}
            </div>
          ))}
        </div>

        {/* Grid */}
        <div className="grid grid-cols-7 gap-px bg-zinc-200/60 dark:bg-zinc-700/60 rounded-xl overflow-hidden border border-zinc-200/60 dark:border-zinc-700/60">
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
                className={`min-h-28 p-2 ${
                  inMonth
                    ? "bg-white/55 dark:bg-zinc-900/55"
                    : "bg-zinc-50/30 dark:bg-zinc-950/30"
                } ${isExpanded ? "ring-2 ring-inset ring-zinc-900/15 dark:ring-zinc-100/20" : ""}`}
              >
                {/* Date row — button when day has screenings */}
                {dayScreenings.length > 0 ? (
                  <button
                    onClick={() => toggleExpanded(key)}
                    aria-expanded={isExpanded}
                    className="w-full flex justify-end items-center gap-0.5 mb-1 cursor-pointer"
                  >
                    {isToday ? (
                      <span className="w-6 h-6 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full flex items-center justify-center text-xs font-semibold">
                        {date.getDate()}
                      </span>
                    ) : (
                      <span className={`text-xs font-medium ${inMonth ? "text-zinc-700 dark:text-zinc-300" : "text-zinc-500 dark:text-zinc-600"}`}>
                        {date.getDate()}
                      </span>
                    )}
                    <span className={`text-[10px] text-zinc-600 dark:text-zinc-500 leading-none transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}>
                      ›
                    </span>
                  </button>
                ) : isToday ? (
                  <div className="flex justify-end mb-1">
                    <span className="w-6 h-6 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full flex items-center justify-center text-xs font-semibold">
                      {date.getDate()}
                    </span>
                  </div>
                ) : (
                  <div className={`text-right text-xs font-medium mb-1 ${inMonth ? "text-zinc-700 dark:text-zinc-300" : "text-zinc-500 dark:text-zinc-600"}`}>
                    {date.getDate()}
                  </div>
                )}

                {/* Screenings */}
                <div className="space-y-0.5">
                  {(isExpanded ? groupByTheatre(dayScreenings) : groupByTheatre(visible)).map((group) => (
                    <div key={group.name} className="border-t border-zinc-50 dark:border-zinc-800 pt-0.5 mt-0.5 first:border-t-0 first:pt-0 first:mt-0">
                      <div className="text-[9px] font-semibold uppercase tracking-widest text-zinc-600/80 dark:text-zinc-400">
                        {group.name}
                      </div>
                      {group.screenings.map((s) => (
                        <ScreeningLink
                          key={s.id}
                          s={s}
                          activeClassName="text-xs leading-snug truncate flex gap-1 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded"
                          onClickScreening={handleScreeningClick}
                          title={`${displayTitle(s.movie.title)} — ${s.theatre.name} — ${formatTime(s.start_time)}`}
                        >
                          <span className="text-zinc-600 dark:text-zinc-400 tabular-nums shrink-0">
                            {formatTime(s.start_time)}
                          </span>
                          <span className="text-zinc-800 dark:text-zinc-200 truncate">
                            {displayTitle(s.movie.title)}
                          </span>
                        </ScreeningLink>
                      ))}
                    </div>
                  ))}
                  {!isExpanded && hidden.length > 0 && (
                    <OverflowBadge groups={groupByTheatre(hidden)} onClickScreening={handleScreeningClick} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {screenings.length === 0 && (
          <p className="text-center text-zinc-600 dark:text-zinc-500 text-sm mt-8">
            No screenings found for this month.
          </p>
        )}
      </main>

      {/* Mobile: agenda list */}
      <main className="md:hidden max-w-7xl mx-auto px-4 py-4">
        {agendaDates.length === 0 ? (
          <p className="text-center text-zinc-600 dark:text-zinc-500 text-sm mt-8">
            No screenings found for this month.
          </p>
        ) : (
          <div className="space-y-3">
            {agendaDates.map((key) => {
              const isExpanded = expandedDay === key;
              const count = byDate[key].length;
              return (
                <section key={key}>
                  <button
                    onClick={() => toggleExpanded(key)}
                    aria-expanded={isExpanded}
                    className={`w-full flex items-center justify-between py-1.5 pb-1.5 border-b text-left ${
                      key === today
                        ? "border-zinc-900 dark:border-zinc-100"
                        : "border-zinc-200 dark:border-zinc-700"
                    }`}
                  >
                    <span className={`text-sm font-semibold ${
                      key === today
                        ? "text-zinc-900 dark:text-zinc-100"
                        : "text-zinc-700 dark:text-zinc-300"
                    }`}>
                      {formatAgendaDate(key, today)}
                    </span>
                    <span className="flex items-center gap-1.5 shrink-0">
                      {!isExpanded && (
                        <span className="text-xs text-zinc-600 dark:text-zinc-400">
                          {count} screening{count !== 1 ? "s" : ""}
                        </span>
                      )}
                      <span className={`text-zinc-600 dark:text-zinc-400 text-sm leading-none transition-transform duration-150 ${isExpanded ? "rotate-90" : ""}`}>
                        ›
                      </span>
                    </span>
                  </button>
                  {isExpanded && (
                    <div className="space-y-3 pt-3">
                      {groupByTheatre(byDate[key]).map((group) => (
                        <div key={group.name}>
                          <div className="text-[9px] font-semibold uppercase tracking-widest text-zinc-600/80 dark:text-zinc-400 mb-1">
                            {group.name}
                          </div>
                          <div className="space-y-0.5">
                            {group.screenings.map((s) => (
                              <ScreeningLink
                                key={s.id}
                                s={s}
                                activeClassName="flex gap-3 items-baseline py-1.5 px-2 -mx-2 rounded active:bg-zinc-100 dark:active:bg-zinc-800"
                                onClickScreening={handleScreeningClick}
                              >
                                <span className="text-xs tabular-nums text-zinc-600 dark:text-zinc-400 shrink-0 w-16">
                                  {formatTime(s.start_time)}
                                </span>
                                <span className="text-sm text-zinc-800 dark:text-zinc-200">
                                  {displayTitle(s.movie.title)}
                                </span>
                              </ScreeningLink>
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

      {modalClickId && (
        <TicketFollowUpModal
          onAnswer={handleModalAnswer}
          onDismiss={handleModalDismiss}
        />
      )}
      {restaurantModal && (
        <RestaurantInterestModal
          theatreName={restaurantModal.theatreName}
          onAnswer={handleRestaurantAnswer}
          onDismiss={handleRestaurantDismiss}
        />
      )}
      {restaurantLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" aria-hidden="true" />
          <div className="relative bg-white dark:bg-zinc-900 rounded-2xl px-8 py-6 shadow-xl border border-zinc-200 dark:border-zinc-700 text-sm text-zinc-600 dark:text-zinc-400">
            Finding restaurants nearby…
          </div>
        </div>
      )}
      {recommendationsModal && (
        <RestaurantRecommendationsModal
          theatreName={recommendationsModal.theatreName}
          restaurants={recommendationsModal.restaurants}
          interestType={recommendationsModal.interestType}
          onClickRestaurant={handleRecommendationClick}
          onDismiss={() => setRecommendationsModal(null)}
        />
      )}
      {calendarSubscribeOpen && (
        <CalendarSubscribeModal
          theatres={theatres}
          initialSlugs={selectedSlugs}
          onClose={() => setCalendarSubscribeOpen(false)}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------

interface TheatreGroup {
  name: string;
  screenings: ScreeningData[];
}

function isPast(startTime: string): boolean {
  return new Date(startTime) < new Date();
}

// ---------------------------------------------------------------------------

interface ScreeningLinkProps {
  s: ScreeningData;
  activeClassName: string;
  onClickScreening: (e: React.MouseEvent<HTMLAnchorElement>, s: ScreeningData) => void;
  title?: string;
  role?: string;
  children: React.ReactNode;
}

function ScreeningLink({ s, activeClassName, onClickScreening, title, role, children }: ScreeningLinkProps) {
  if (isPast(s.start_time)) {
    return (
      <span
        role={role}
        title={title}
        className={`${activeClassName} opacity-40 cursor-default`}
      >
        {children}
      </span>
    );
  }
  return (
    <a
      href={screeningUrl(s)}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => onClickScreening(e, s)}
      role={role}
      title={title}
      className={activeClassName}
    >
      {children}
    </a>
  );
}

// ---------------------------------------------------------------------------

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
  onClickScreening: (e: React.MouseEvent<HTMLAnchorElement>, s: ScreeningData) => void;
}

function OverflowBadge({ groups, onClickScreening }: OverflowBadgeProps) {
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
        className="text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300 hover:underline cursor-pointer focus:outline-none focus-visible:underline"
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
            className="z-50 min-w-52 max-w-72 rounded-lg border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 py-2 shadow-lg"
          >
            {groups.map((group) => (
              <div key={group.name} className="border-t border-zinc-100 dark:border-zinc-800 first:border-t-0">
                <div className="px-3 pt-1 pb-0.5 text-[10px] uppercase tracking-wider text-zinc-600 dark:text-zinc-400 font-medium">
                  {group.name}
                </div>
                {group.screenings.map((s) => (
                  <ScreeningLink
                    key={s.id}
                    s={s}
                    role="listitem"
                    activeClassName="flex items-baseline gap-2 px-3 py-0.5 text-xs hover:bg-zinc-50 dark:hover:bg-zinc-800"
                    onClickScreening={onClickScreening}
                    title={`${displayTitle(s.movie.title)} — ${s.theatre.name}`}
                  >
                    <span className="shrink-0 tabular-nums text-zinc-600 dark:text-zinc-400">
                      {formatTime(s.start_time)}
                    </span>
                    <span className="truncate text-zinc-700 dark:text-zinc-300">
                      {displayTitle(s.movie.title)}
                    </span>
                  </ScreeningLink>
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
            ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900"
            : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300"
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
          className="absolute top-full left-0 right-0 mt-1.5 z-50 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-lg overflow-hidden"
        >
          <label className="flex items-center gap-3 px-4 py-3 border-b border-zinc-100 dark:border-zinc-800 cursor-pointer active:bg-zinc-50 dark:active:bg-zinc-800">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onSelectAll}
              className="w-4 h-4 accent-zinc-900 dark:accent-zinc-400"
            />
            <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">All Theatres</span>
          </label>

          <div className="max-h-64 overflow-y-auto">
            {theatres.map((t) => (
              <label
                key={t.slug}
                className={`flex items-center gap-3 px-4 py-3 border-b border-zinc-50 dark:border-zinc-800 last:border-b-0 ${
                  t.is_cron_enabled
                    ? "cursor-pointer active:bg-zinc-50 dark:active:bg-zinc-800"
                    : "cursor-not-allowed opacity-60"
                }`}
                title={!t.is_cron_enabled ? "Scraper temporarily unavailable" : undefined}
              >
                <input
                  type="checkbox"
                  checked={selectedSlugs.has(t.slug)}
                  onChange={() => t.is_cron_enabled && onToggle(t.slug)}
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

          <div className="px-4 py-3 border-t border-zinc-100 dark:border-zinc-800">
            <button
              onClick={() => setOpen(false)}
              className="w-full py-2 text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-lg"
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
  disabled = false,
  onClick,
}: {
  label: string;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  if (disabled) {
    return (
      <span
        title="Scraper temporarily unavailable"
        className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-500 cursor-not-allowed"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
        {label}
      </span>
    );
  }
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
        active
          ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900"
          : "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
      }`}
    >
      {label}
    </button>
  );
}

// ---------------------------------------------------------------------------

function ThemeToggle() {
  function toggle() {
    const isDark = document.documentElement.classList.toggle("dark");
    try {
      localStorage.setItem("theme", isDark ? "dark" : "light");
    } catch {}
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle dark mode"
      className="ml-1 p-1.5 rounded-lg text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
    >
      {/* Moon: visible in light mode */}
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="block dark:hidden">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
      {/* Sun: visible in dark mode */}
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="hidden dark:block">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    </button>
  );
}
