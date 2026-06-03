import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export function useComplaints() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComplaints = async () => {
      try {
        // const data = await api.get("/complaints");
        // setComplaints(data.items);
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch complaints", error);
        setLoading(false);
      }
    };
    fetchComplaints();
  }, []);

  return { complaints, loading };
}
