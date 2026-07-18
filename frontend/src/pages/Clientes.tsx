import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, Edit2, Trash2, ChevronLeft, ChevronRight, UserPlus, X, ArrowUp, ArrowDown, ArrowUpDown, Upload, FileSpreadsheet, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import { useClientes } from '../hooks/useClientes';
import { clientesApi, type Cliente } from '../api/clientes';
import ClienteDrawer from '../components/ClienteModal';

const ClientesPage: React.FC = () => {
  const { clientes, loading, total, params, updateParams, fetchClientes } = useClientes();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCliente, setEditingCliente] = useState<Cliente | null>(null);
  const [searchTerm, setSearchTerm] = useState(params.search);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Debounce search to avoid API hammering
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchTerm !== params.search) {
        updateParams({ search: searchTerm });
      }
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validar extensión
    if (!file.name.endsWith('.xlsx')) {
      toast.error('Formato inválido. Solo se permiten archivos .xlsx');
      return;
    }

    // Validar tamaño (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('El archivo es demasiado grande. Máximo 10MB');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      toast.loading('Importando clientes...');
      const response = await fetch('/api/clientes/import', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (result.status_code === 200) {
        const data = result.data;
        toast.dismiss();
        toast.success(`Importación completada: ${data.registros_exitosos}/${data.total_registros} exitosos`);
        if (data.registros_fallidos > 0) {
          toast.error(`${data.registros_fallidos} registros fallaron`);
        }
        fetchClientes();
      } else {
        toast.dismiss();
        toast.error(result.message || 'Error al importar clientes');
      }
    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message || 'Error al importar clientes');
    }

    // Resetear input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const downloadTemplate = () => {
    const link = document.createElement('a');
    link.href = '/plantilla_clientes.xlsx';
    link.download = 'plantilla_clientes.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Plantilla descargada');
  };

  const handleCreate = async (data: any) => {
    try {
      const res = await clientesApi.create(data);
      if (res.status_code === 201 || res.status_code === 200) {
        toast.success('Cliente creado exitosamente');
        setIsModalOpen(false);
        fetchClientes();
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al crear cliente');
    }
  };

  const handleUpdate = async (data: any) => {
    if (!editingCliente) return;
    try {
      const res = await clientesApi.update(editingCliente.id, data);
      if (res.status_code === 200) {
        toast.success('Cliente actualizado exitosamente');
        setIsModalOpen(false);
        setEditingCliente(null);
        fetchClientes();
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al actualizar cliente');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que deseas eliminar este cliente? Esta acción desactivará el registro.')) {
      return;
    }
    try {
      const res = await clientesApi.delete(id);
      if (res.status_code === 200) {
        toast.success('Cliente eliminado exitosamente');
        fetchClientes();
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al eliminar cliente');
    }
  };

  const openCreateModal = () => {
    setEditingCliente(null);
    setIsModalOpen(true);
  };

  const openEditModal = (cliente: Cliente) => {
    setEditingCliente(cliente);
    setIsModalOpen(true);
  };

  // Pagination logic
  const totalPages = Math.ceil(total / params.limit);
  const currentPage = Math.floor(params.offset / params.limit) + 1;

  const goToPage = (page: number) => {
    const newOffset = (page - 1) * params.limit;
    updateParams({ offset: newOffset });
  };

  const handleSort = (column: string) => {
    const isCurrentColumn = params.sort_by === column;
    const currentOrder = params.sort_order;

    let nextOrder = 'asc';
    if (isCurrentColumn) {
      nextOrder = currentOrder === 'asc' ? 'desc' : 'asc';
    }

    updateParams({
      sort_by: column,
      sort_order: nextOrder
    });
  };

  const getSortIcon = (column: string) => {
    if (params.sort_by !== column) return <ArrowUpDown className="w-3 h-3 inline-block ml-1 text-slate-300" />;
    return params.sort_order === 'asc'
      ? <ArrowUp className="w-3 h-3 inline-block ml-1 text-vortex-primary" />
      : <ArrowDown className="w-3 h-3 inline-block ml-1 text-vortex-primary" />;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Gestión de Clientes</h1>
          <p className="text-slate-500 text-sm">Administra la información de tus clientes y sus límites de crédito.</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={downloadTemplate}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-white text-vortex-primary border border-vortex-primary rounded-lg font-bold hover:bg-vortex-primary/10 transition-all shadow-sm active:scale-95"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Plantilla</span>
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg font-bold hover:bg-emerald-700 transition-all shadow-md shadow-emerald-600/20 active:scale-95"
          >
            <Upload className="w-4 h-4" />
            <span className="text-sm">Importar Excel</span>
          </button>
          <button
            onClick={openCreateModal}
            className="flex items-center justify-center space-x-2 px-4 py-2 bg-vortex-primary text-white rounded-lg font-bold hover:bg-vortex-secondary transition-all shadow-md shadow-vortex-primary/20 active:scale-95"
          >
            <UserPlus className="w-4 h-4" />
            <span className="text-sm">Nuevo Cliente</span>
          </button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por código, RIF o nombre..."
            className="w-full pl-10 pr-10 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary transition-all text-sm"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-100 rounded-full transition-colors"
              title="Limpiar búsqueda"
            >
              <X className="w-3 h-3 text-slate-400" />
            </button>
          )}
        </div>
        <div className="flex items-center space-x-6 w-full md:w-auto">
          <div className="flex items-center space-x-3">
            <span className="text-sm text-slate-500 font-medium">Mostrar activos:</span>
            <button
              onClick={() => updateParams({ activo: !params.activo })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${params.activo ? 'bg-vortex-primary' : 'bg-slate-300'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${params.activo ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>
          <div className="flex items-center space-x-2 border-l border-slate-200 pl-6">
            <span className="text-sm text-slate-500 font-medium">Registros:</span>
            <select
              value={params.limit}
              onChange={(e) => updateParams({ limit: Number(e.target.value) })}
              className="px-2 py-1 text-xs font-medium border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary transition-all bg-white text-slate-600"
            >
              {[5, 10, 20, 50, 100].map(size => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-slate-600">
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('codigo')}
                >
                  Código {getSortIcon('codigo')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('rif')}
                >
                  RIF {getSortIcon('rif')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('nombre_razon_social')}
                >
                  Nombre / Razón Social {getSortIcon('nombre_razon_social')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('condicion')}
                >
                  Condición {getSortIcon('condicion')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('credito')}
                >
                  Límite Crédito {getSortIcon('credito')}
                </th>
                <th className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr className="bg-white">
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="w-8 h-8 border-4 border-slate-200 border-t-vortex-primary rounded-full animate-spin"></div>
                      <p className="text-slate-400 text-sm font-medium">Cargando clientes...</p>
                    </div>
                  </td>
                </tr>
              ) : clientes.length > 0 ? (
                clientes.map((cliente) => (
                  <tr key={cliente.id} className="hover:bg-vortex-primary/5 transition-colors group even:bg-slate-50/50 odd:bg-white">
                    <td className="px-4 py-2 text-xs font-medium text-slate-700 border-r border-slate-200">{cliente.codigo}</td>
                    <td className="px-4 py-2 text-xs text-slate-600 border-r border-slate-200">{cliente.rif}</td>
                    <td className="px-4 py-2 text-xs font-semibold text-slate-800 border-r border-slate-200">{cliente.nombre_razon_social}</td>
                    <td className="px-4 py-2 text-xs border-r border-slate-200">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                        cliente.condicion_pago === 'CREDITO' ? 'bg-blue-100 text-blue-700' :
                        cliente.condicion_pago === 'ANTICIPO' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {cliente.condicion_pago}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-slate-600 border-r border-slate-200">
                      {new Intl.NumberFormat('es-VE', { style: 'currency', currency: 'VES' }).format(cliente.limite_credito)}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => openEditModal(cliente)}
                          className="p-2 text-vortex-primary bg-white border border-slate-200 rounded-lg shadow-sm hover:bg-vortex-primary hover:text-white transition-all active:scale-90"
                          title="Editar"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(cliente.id)}
                          className="p-2 text-red-500 bg-white border border-slate-200 rounded-lg shadow-sm hover:bg-red-500 hover:text-white transition-all active:scale-90"
                          title="Eliminar"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr className="bg-white">
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="p-3 bg-slate-100 rounded-full">
                        <Search className="w-6 h-6 text-slate-400" />
                      </div>
                      <p className="text-slate-500 text-sm font-medium">No se encontraron clientes</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <p className="text-[11px] text-slate-500 font-medium">
            Mostrando <span className="text-slate-800 font-bold">{clientes.length}</span> de <span className="text-slate-800 font-bold">{total}</span> registros
          </p>
          <div className="flex items-center space-x-1">
            <button
              disabled={currentPage === 1}
              onClick={() => goToPage(currentPage - 1)}
              className="p-1 text-slate-400 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-all border border-slate-200 bg-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-1 mx-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => goToPage(page)}
                  className={`px-2.5 py-1 text-xs font-medium rounded transition-all border ${
                    currentPage === page
                    ? 'bg-vortex-primary text-white border-vortex-primary shadow-sm'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-vortex-primary hover:text-vortex-primary'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>

            <button
              disabled={currentPage === totalPages}
              onClick={() => goToPage(currentPage + 1)}
              className="p-1 text-slate-400 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed rounded transition-all border border-slate-200 bg-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <ClienteDrawer
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingCliente(null);
        }}
        initialData={editingCliente}
        onSubmit={editingCliente ? handleUpdate : handleCreate}
      />
    </div>
  );
};

export default ClientesPage;
