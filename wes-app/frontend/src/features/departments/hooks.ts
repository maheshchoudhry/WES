import { useQuery } from '@tanstack/react-query';
import { listDepartments } from '@/features/departments/api';

export function useDepartments() {
  return useQuery({ queryKey: ['departments'], queryFn: listDepartments });
}
