import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface LiveEmployee {
  id: string;
  name: string;
  code: string;
  role: string;
  department: string;
  authority: string;
  provider: string;
  status: string;
  current_task: string | null;
}

export interface LiveCompany {
  employees: LiveEmployee[];
  counts: {
    working: number;
    waiting: number;
    blocked: number;
    idle: number;
    projects: number;
    sprints: number;
    tasks_in_progress: number;
    queue_length: number;
    running_jobs: number;
  };
  pipeline_status: string | null;
  provider: string;
  repository: string | null;
}

export interface TimelineEvent {
  at: string;
  actor: string | null;
  type: string;
  title: string;
  detail?: string;
}

export interface Conversation {
  at: string;
  from: string | null;
  to: string | null;
  from_role: string | null;
  to_role: string | null;
  stage: string | null;
  message: string | null;
  task: string | null;
  status: string;
}

export interface EmployeeWorkspace {
  profile: {
    id: string;
    name: string;
    code: string;
    role: string;
    department: string;
    authority: string;
    provider: string;
    status: string;
  };
  current: {
    task: string | null;
    task_title: string | null;
    project: string | null;
    sprint: number | null;
    branch: string | null;
    repository: string | null;
    context: string | null;
  };
  performance: {
    assigned: number;
    in_progress: number;
    done: number;
    stages_performed: number;
  };
  inbox: {
    task_code: string;
    title: string;
    project: string | null;
    sender: string | null;
    priority: string;
    received: string | null;
    deadline: string | null;
    repository: string | null;
    status: string;
    estimated_hours: number | null;
  }[];
  tasks: Record<string, string[]>;
  decisions: {
    at: string | null;
    decision: string;
    stage: string;
    reason: string | null;
    provider: string | null;
    status: string;
  }[];
  handoffs: {
    at: string | null;
    from: string | null;
    to: string | null;
    reason: string | null;
    stage: string | null;
    result: string;
  }[];
  memory: {
    id: string;
    scope: string;
    kind: string;
    summary: string;
    created_at: string | null;
  }[];
}

export const companyApi = {
  live: () => http.get<DataResponse<LiveCompany>>("/company/live"),
  timeline: (limit = 120) =>
    http.get<ListResponse<TimelineEvent>>(`/company/timeline?limit=${limit}`),
  conversations: (limit = 100) =>
    http.get<ListResponse<Conversation>>(`/company/conversations?limit=${limit}`),
  workspace: (employeeId: string) =>
    http.get<DataResponse<EmployeeWorkspace>>(`/company/employees/${employeeId}/workspace`),
};
