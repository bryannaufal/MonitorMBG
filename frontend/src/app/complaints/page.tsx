import { redirect } from "next/navigation";

export default function ComplaintsAliasPage() {
  redirect("/intake?tab=complaints");
}
