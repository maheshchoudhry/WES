import { useQuery } from '@tanstack/react-query';
import { listCompanies } from '@/features/company/api';

export function useCompanies() {
  return useQuery({ queryKey: ['companies'], queryFn: listCompanies });
}
