import { api, Page } from '@/lib/api-client';
import { Department } from '@/features/departments/types';

export const listDepartments = () => api.get<Page<Department>>('/departments');
