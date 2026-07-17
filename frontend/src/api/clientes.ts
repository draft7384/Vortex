import { api } from './client';
import type { Cliente, APIResponse, PagedResponse } from '../types/api';

export type { Cliente };

export const clientesApi = {
  async list(params: { search?: string; activo?: boolean; limit?: number; offset?: number }): Promise<APIResponse<PagedResponse<Cliente>>> {
    return await api.get<any, APIResponse<PagedResponse<Cliente>>>('/clientes/', { params });
  },

  async get(id: number): Promise<APIResponse<Cliente>> {
    return await api.get<any, APIResponse<Cliente>>(`/clientes/${id}`);
  },

  async create(data: Partial<Cliente>): Promise<APIResponse<Cliente>> {
    return await api.post<any, APIResponse<Cliente>>('/clientes/', data);
  },

  async update(id: number, data: Partial<Cliente>): Promise<APIResponse<Cliente>> {
    return await api.put<any, APIResponse<Cliente>>(`/clientes/${id}`, data);
  },

  async delete(id: number): Promise<APIResponse<null>> {
    return await api.delete<any, APIResponse<null>>(`/clientes/${id}`);
  },
};