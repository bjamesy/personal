// Server-side API URL (Docker internal). Falls back to NEXT_PUBLIC for local dev.
const API_URL =
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

// Client-side API URL — always uses the public env var.
const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface TheatreData {
  id: string;
  name: string;
  slug: string;
  source_url: string;
  is_cron_enabled: boolean;
}

export interface MovieData {
  id: string;
  title: string;
}

export interface ScreeningData {
  id: string;
  theatre: TheatreData;
  movie: MovieData;
  start_time: string;
  end_time: string | null;
  raw_source_ref: string | null;
  created_at: string;
}

export async function fetchTheatres(): Promise<TheatreData[]> {
  try {
    const res = await fetch(`${API_URL}/theatres`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export type TicketConfirmedStatus = "yes" | "no" | "not_yet";

export interface OutboundClickData {
  id: string;
  screening_id: string;
  created_at: string;
  ticket_confirmed: TicketConfirmedStatus | null;
  prompted_at: string | null;
}

export async function recordOutboundClick(
  screening_id: string
): Promise<OutboundClickData | null> {
  try {
    const res = await fetch(`${PUBLIC_API_URL}/outbound-clicks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ screening_id }),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export type RestaurantInterestType = "before_movie" | "after_movie" | "browsing" | "declined";

export interface RestaurantResult {
  name: string;
  rating: number | null;
  address: string | null;
  google_maps_url: string | null;
  place_id: string | null;
  place_metadata: Record<string, unknown> | null;
}

export async function fetchRestaurants(
  theatreId: string,
  intent: RestaurantInterestType
): Promise<RestaurantResult[]> {
  try {
    const res = await fetch(
      `${PUBLIC_API_URL}/theatres/${theatreId}/restaurants?intent=${intent}`,
      { signal: AbortSignal.timeout(10000) }
    );
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function recordRecommendationClick(
  screening_id: string,
  outbound_click_id: string | null,
  restaurant_name: string,
  interest_type: RestaurantInterestType,
  place_id: string | null,
  place_metadata: Record<string, unknown> | null
): Promise<void> {
  try {
    await fetch(`${PUBLIC_API_URL}/restaurant-recommendation-clicks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ screening_id, outbound_click_id, restaurant_name, interest_type, place_id, place_metadata }),
    });
  } catch {
    // best-effort
  }
}

export async function recordRestaurantInterest(
  outbound_click_id: string,
  interest_type: RestaurantInterestType
): Promise<void> {
  try {
    await fetch(`${PUBLIC_API_URL}/restaurant-interest-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outbound_click_id, interest_type }),
    });
  } catch {
    // best-effort
  }
}

export async function patchOutboundClick(
  id: string,
  body: { ticket_confirmed?: TicketConfirmedStatus; prompted_at?: string }
): Promise<void> {
  try {
    await fetch(`${PUBLIC_API_URL}/outbound-clicks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    // best-effort
  }
}

export async function fetchScreenings(month: string): Promise<ScreeningData[]> {
  try {
    const res = await fetch(`${API_URL}/screenings?month=${month}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export interface CalendarSubscriptionResponse {
  token: string;
  feed_url: string;
}

export async function createCalendarSubscription(
  theatre_ids: string[],
  label?: string
): Promise<CalendarSubscriptionResponse | null> {
  try {
    const res = await fetch(`${PUBLIC_API_URL}/calendar-subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theatre_ids, label }),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
