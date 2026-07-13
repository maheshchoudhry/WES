import { api, Page } from '@/lib/api-client';
import { Employee } from '@/features/employees/types';

export const listEmployees = (departmentId?: number) => {
  const query = departmentId ? `?departmentId=${departmentId}` : '';
  return api.get<Page<Employee>>(`/employees${query}`);
};
