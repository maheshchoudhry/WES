import { useQuery } from '@tanstack/react-query';
import { getSystemMetadata } from '@/features/system/api';

export function useSystemMetadata() {
  return useQuery({ queryKey: ['system-metadata'], queryFn: getSystemMetadata });
}
