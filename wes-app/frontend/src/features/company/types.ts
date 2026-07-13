export interface Company {
  id: number;
  name: string;
  legalType: string;
  purpose: string | null;
  mission: string | null;
  description: string | null;
  status: string;
  settings: Record<string, unknown>;
  version: string;
  createdAt: string;
  updatedAt: string;
}
