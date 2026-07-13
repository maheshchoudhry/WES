import { api } from '@/lib/api-client';
import { SystemMetadata } from '@/features/system/types';

export const getSystemMetadata = async (): Promise<SystemMetadata> => {
  const res = await api.get<{ data: SystemMetadata }>('/system/metadata');
  return res.data;
};
