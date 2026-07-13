export interface SystemMetadata {
  appName: string;
  apiVersion: string;
  schemaVersion: string;
  counts: {
    companies: number;
    departments: number;
    employees: number;
  };
}
