import { useQuery } from '@tanstack/react-query';
import { listEmployees } from '@/features/employees/api';

export function useEmployees(departmentId?: number) {
  return useQuery({
    queryKey: ['employees', departmentId ?? 'all'],
    queryFn: () => listEmployees(departmentId),
  });
}
