import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export function useNutrition(reportId: number) {
  const [nutrition, setNutrition] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNutrition = async () => {
      try {
        // const data = await api.get(`/nutrition/report/${reportId}`);
        // setNutrition(data);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch nutrition data", error);
        setLoading(false);
      }
    };
    if (reportId) fetchNutrition();
  }, [reportId]);

  return { nutrition, loading };
}
