import { redirect } from "next/navigation";

export default function ReportsAliasPage() {
  redirect("/intake?tab=reports");
}
