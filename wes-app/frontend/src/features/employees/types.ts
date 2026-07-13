export interface Employee {
  id: number;
  employeeCode: string;
  name: string;
  position: string;
  departmentId: number | null;
  departmentName: string | null;
  reportsTo: string | null;
  authorityLevel: string;
  status: string;
  availabilityStatus: string;
  operationalState: string;
  version: string;
  createdAt: string;
  updatedAt: string;
}
