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
  theatre_id: string;
  clicked_at: string;
  ticket_confirmed: TicketConfirmedStatus | null;
  prompted_at: string | null;
}

export async function recordOutboundClick(
  screening_id: string,
  theatre_id: string
): Promise<OutboundClickData | null> {
  try {
    const res = await fetch(`${PUBLIC_API_URL}/outbound-clicks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ screening_id, theatre_id }),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
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
