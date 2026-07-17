import { useState, useEffect } from 'react';
import { clientesApi } from '../api/clientes';
import type { Cliente } from '../types/api';
import toast from 'react-hot-toast';

export function useClientes() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [params, setParams] = useState({
    search: '',
    activo: true,
    limit: 10,
    offset: 0,
    sort_by: 'nombre_razon_social',
    sort_order: 'asc'
  });

  const fetchClientes = async (currentParams = params) => {
    setLoading(true);
    try {
      const response = await clientesApi.list(currentParams);
      if (response.status_code === 200) {
        setClientes(response.data.items);
        setTotal(response.data.total);
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al cargar clientes');
    } finally {
      setLoading(false);
    }
  };

  // This effect handles ALL data fetching based on params changes
  useEffect(() => {
    fetchClientes();
  }, [params]); // Trigger whenever any parameter (search, activo, offset, sort_by, sort_order) changes

  const updateParams = (updates: Partial<typeof params>) => {
    setParams(prev => {
      const nextParams = { ...prev, ...updates };
      // Reset offset to 0 whenever search, active filter or limit changes
      if (updates.search !== undefined || updates.activo !== undefined || updates.limit !== undefined) {
        nextParams.offset = 0;
      }
      return nextParams;
    });
  };

  return {
    clientes,
    loading,
    total,
    params,
    updateParams,
    fetchClientes
  };
}
