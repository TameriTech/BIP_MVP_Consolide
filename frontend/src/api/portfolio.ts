import { http } from "./http";
import type { Performance, Portfolio, PositionView } from "./types";

export const portfolioApi = {
  getMine: () => http.get<Portfolio>("/portfolio/me").then((r) => r.data),
  getMyPositions: () => http.get<PositionView[]>("/portfolio/me/positions").then((r) => r.data),
  getMyPerformance: () => http.get<Performance>("/portfolio/me/performance").then((r) => r.data),
};
