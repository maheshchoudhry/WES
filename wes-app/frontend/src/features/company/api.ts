import { api, Page } from '@/lib/api-client';
import { Company } from '@/features/company/types';

export const listCompanies = () => api.get<Page<Company>>('/companies');
