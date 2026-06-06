import { redirect } from "next/navigation";

export default function DailyReportsAliasPage() {
  redirect("/intake?tab=daily-reports");
}
