import axios from "axios";

const API_BASE = (import.meta.env.VITE_API_BASE as string) || "";
const api = axios.create({ baseURL: API_BASE });

export const getStrategies = () => api.get("/api/strategies").then((r) => r.data);
export const getSchedule = () => api.get("/api/demo/schedule").then((r) => r.data);
export const getSimulate = (strategy: string) =>
  api.get("/api/demo/simulate", { params: { strategy } }).then((r) => r.data);
export const getCompare = () => api.get("/api/demo/compare").then((r) => r.data);
export const getFrontier = () => api.get("/api/demo/frontier").then((r) => r.data);
export const getMonteCarlo = (strategy: string, n_paths = 400) =>
  api.get("/api/demo/montecarlo", { params: { strategy, n_paths } }).then((r) => r.data);
