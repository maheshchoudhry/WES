import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface Notification {
  id: string;
  kind: string;
  title: string;
  message: string | null;
  severity: string;
  entity_type: string | null;
  entity_id: string | null;
  read: boolean;
  created_at: string | null;
}

export const notificationsApi = {
  list: (unread = false) =>
    http.get<ListResponse<Notification>>(`/notifications${unread ? "?unread=true" : ""}`),
  unreadCount: () => http.get<DataResponse<{ unread: number }>>("/notifications/unread-count"),
  markRead: (id: string) => http.post<DataResponse<Notification>>(`/notifications/${id}/read`, {}),
  markAllRead: () => http.post<DataResponse<{ marked: number }>>("/notifications/read-all", {}),
};
