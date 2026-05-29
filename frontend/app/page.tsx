import { CalendarView } from "@/components/CalendarView";
import { fetchScreenings, fetchTheatres } from "@/lib/api";
import { currentMonth } from "@/lib/utils";

const MONTH_RE = /^\d{4}-(0[1-9]|1[0-2])$/;

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ month?: string }>;
}) {
  const { month: rawMonth } = await searchParams;
  const month =
    rawMonth && MONTH_RE.test(rawMonth) ? rawMonth : currentMonth();

  const [theatres, screenings] = await Promise.all([
    fetchTheatres(),
    fetchScreenings(month),
  ]);

  return (
    <CalendarView theatres={theatres} screenings={screenings} month={month} />
  );
}
