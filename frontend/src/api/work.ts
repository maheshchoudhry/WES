import type { DataResponse, ListResponse } from "../types";
import { http } from "./client";

export interface Project {
  id: string;
  code: string;
  name: string;
  owner_ai_employee_id: string | null;
  owner_name: string | null;
  status: string;
  priority: string;
  repository: string | null;
  tech_stack: string | null;
  version: number;
  task_count: number;
  business_objective?: string | null;
  plan_status?: string | null;
  created_at: string;
  updated_at: string;
}

// Founder Project Intake (WP6, Phase 1).
export interface ProjectIntakeInput {
  code: string;
  name: string;
  priority?: string;
  repository?: string;
  business_objective?: string;
  business_problem?: string;
  intake_description?: string;
  acceptance_criteria?: string;
  deliverables?: string[];
  constraints?: string[];
  timeline?: string;
  founder_notes?: string;
}

export interface ProjectPlan {
  project: {
    id: string;
    code: string;
    name: string;
    business_objective: string | null;
    plan_status: string | null;
    status: string;
  };
  business_analysis: {
    analyst: string;
    vision: string;
    scope: { in_scope: string[]; out_of_scope: string[] };
    risks: string[];
    architecture_proposal: string;
  } | null;
  epics: { id: string; name: string; status: string }[];
  sprints: { sprint_number: number; goal: string | null; status: string }[];
  tasks: {
    task_code: string;
    title: string;
    assignee: string | null;
    reviewer: string | null;
    estimated_hours: number | null;
    status: string;
  }[];
  totals: { epics: number; sprints: number; tasks: number; estimated_hours: number };
}

export interface Sprint {
  id: string;
  project_id: string;
  sprint_number: number;
  goal: string | null;
  start_date: string | null;
  end_date: string | null;
  status: string;
  velocity: number;
  task_count: number;
  done_count: number;
}

export interface Milestone {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  due_date: string | null;
  status: string;
}

export interface WorkItem {
  id: string;
  task_code: string;
  title: string;
  description: string | null;
  acceptance_criteria: string | null;
  priority: string;
  status: string;
  estimated_hours: number | null;
  actual_hours: number | null;
  project_id: string;
  project_code: string | null;
  sprint_id: string | null;
  sprint_number: number | null;
  milestone_id: string | null;
  milestone_name: string | null;
  assigned_ai_employee_id: string | null;
  assigned_name: string | null;
  reviewer_ai_employee_id: string | null;
  reviewer_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface KanbanColumn {
  status: string;
  count: number;
  tasks: WorkItem[];
}

export interface Assignment {
  id: string;
  work_item_id: string;
  ai_employee_id: string;
  ai_employee_name: string | null;
  role: string;
  assigned_by: string | null;
  created_at: string;
}

export interface ActivityEntry {
  id: string;
  project_id: string | null;
  work_item_id: string | null;
  actor: string;
  action: string;
  detail: string | null;
  created_at: string;
}

export interface FounderWorkSummary {
  total_projects: number;
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  tasks_by_priority: Record<string, number>;
  blocked_tasks: number;
  sprint_progress: {
    sprint_number: number;
    status: string;
    total: number;
    done: number;
    velocity: number;
  }[];
  velocity: number;
  upcoming_deadlines: { name: string; due_date: string; status: string }[];
  ai_workload: Record<string, number>;
}

export interface AIWorkSummary {
  assigned_work: number;
  current_tasks: number;
  completed_work: number;
  team_capacity: { team_size: number; open_tasks: number; avg_load: number };
  work_distribution: Record<string, number>;
  department_load: Record<string, number>;
}

export const workApi = {
  projects: () => http.get<ListResponse<Project>>("/projects"),
  project: (id: string) => http.get<DataResponse<Project>>(`/projects/${id}`),
  createProject: (input: ProjectIntakeInput) =>
    http.post<DataResponse<Project>>("/projects", input),
  decompose: (projectId: string) =>
    http.post<DataResponse<ProjectPlan>>(`/projects/${projectId}/decompose`, {}),
  plan: (projectId: string) =>
    http.get<DataResponse<ProjectPlan>>(`/projects/${projectId}/plan`),
  approvePlan: (projectId: string) =>
    http.post<DataResponse<ProjectPlan>>(`/projects/${projectId}/approve-plan`, {}),
  sprints: (projectId: string) => http.get<ListResponse<Sprint>>(`/projects/${projectId}/sprints`),
  milestones: (projectId: string) =>
    http.get<ListResponse<Milestone>>(`/projects/${projectId}/milestones`),
  tasks: (params: { projectId?: string; status?: string; search?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.status) q.set("status", params.status);
    if (params.search) q.set("search", params.search);
    q.set("page_size", "200");
    return http.get<ListResponse<WorkItem>>(`/tasks?${q.toString()}`);
  },
  task: (id: string) => http.get<DataResponse<WorkItem>>(`/tasks/${id}`),
  updateTask: (id: string, input: Partial<{ status: string; priority: string; title: string }>) =>
    http.patch<DataResponse<WorkItem>>(`/tasks/${id}`, input),
  assignTask: (id: string, aiEmployeeId: string, role = "assignee") =>
    http.post<DataResponse<WorkItem>>(`/tasks/${id}/assign`, {
      ai_employee_id: aiEmployeeId,
      role,
    }),
  taskAssignments: (id: string) => http.get<ListResponse<Assignment>>(`/tasks/${id}/assignments`),
  kanban: (projectId?: string) =>
    http.get<DataResponse<KanbanColumn[]>>(
      `/work/kanban${projectId ? `?project_id=${projectId}` : ""}`,
    ),
  founderSummary: () => http.get<DataResponse<FounderWorkSummary>>("/work/founder-summary"),
  aiSummary: () => http.get<DataResponse<AIWorkSummary>>("/work/ai-summary"),
  activity: (params: { projectId?: string; workItemId?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.projectId) q.set("project_id", params.projectId);
    if (params.workItemId) q.set("work_item_id", params.workItemId);
    return http.get<ListResponse<ActivityEntry>>(`/activity?${q.toString()}`);
  },
};

export const KANBAN_ORDER = [
  "backlog",
  "planned",
  "assigned",
  "in_progress",
  "review",
  "testing",
  "done",
];
