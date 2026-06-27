import { useQuery } from "@tanstack/react-query";

import { fetchDashboardData } from "../data/mockDashboardData";

export function useDashboardData() {
  return useQuery({
    queryKey: ["dashboard-data"],
    queryFn: fetchDashboardData,
    staleTime: 30_000,
  });
}
