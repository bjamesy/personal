// Server-side API URL (Docker internal). Falls back to NEXT_PUBLIC for local dev.
const API_URL =
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

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
