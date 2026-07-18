/**
 * Pagina de Gestion de Productos
 * Diseño moderno idéntico a Clientes con panel lateral deslizante
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Plus, Edit2, Trash2, ArrowUp, ArrowDown, ArrowUpDown,
  Upload, Download, Package, Eye, EyeOff, X, ChevronLeft, ChevronRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import ProductoDrawer from '../components/ProductoModal';

interface Producto {
  id: number;
  codigo: string;
  descripcion: string;
  unidad_medida: string;
  precio_base: number;
  impuesto_pct: number;
  existencia: number;
  es_servicio: boolean;
  activo: boolean;
}

const ProductosPage: React.FC = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProducto, setEditingProducto] = useState<Producto | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showInactive, setShowInactive] = useState(false);
  const [params, setParams] = useState({
    limit: 10,
    offset: 0,
    search: '',
    sort_by: 'codigo',
    sort_order: 'asc'
  });
  const [total, setTotal] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cargar productos
  useEffect(() => {
    fetchProductos();
  }, [params]);

  const fetchProductos = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const queryParams = new URLSearchParams({
        limit: params.limit.toString(),
        offset: params.offset.toString(),
        search: params.search,
        sort_by: params.sort_by,
        sort_order: params.sort_order
      });
      
      const response = await fetch(`http://localhost:8000/productos/?${queryParams}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      if (data.status === 200) {
        setProductos(data.data.items || []);
        setTotal(data.data.total || 0);
      }
    } catch (error) {
      console.error('Error al cargar productos:', error);
      toast.error('Error al cargar productos');
    } finally {
      setLoading(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchTerm !== params.search) {
        setParams(prev => ({ ...prev, search: searchTerm, offset: 0 }));
      }
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx')) {
      toast.error('Formato inválido. Solo se permiten archivos .xlsx');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('El archivo es demasiado grande. Máximo 10MB');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      toast.loading('Importando productos...');
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/productos/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      
      if (result.status === 200 || result.status_code === 200) {
        const data = result.data;
        toast.dismiss();
        toast.success(`Importación completada: ${data.registros_exitosos || data.exitosos}/${data.total_registros || (data.exitosos + data.fallidos)} exitosos`);
        if ((data.registros_fallidos || data.fallidos) > 0) {
          toast.error(`${data.registros_fallidos || data.fallidos} registros fallaron`);
        }
        fetchProductos();
      } else {
        toast.dismiss();
        toast.error(result.message || 'Error al importar productos');
      }
    } catch (error: any) {
      toast.dismiss();
      toast.error(error.message || 'Error al importar productos');
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const downloadTemplate = () => {
    const link = document.createElement('a');
    link.href = '/plantilla_productos.xlsx';
    link.download = 'plantilla_productos.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Plantilla descargada');
  };

  const handleSaveProducto = async (data: any) => {
    try {
      const token = localStorage.getItem('token');
      const url = editingProducto 
        ? `http://localhost:8000/productos/${editingProducto.id}`
        : 'http://localhost:8000/productos/';
      
      const method = editingProducto ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      
      if (result.status === 200 || result.status === 201 || result.status_code === 200 || result.status_code === 201) {
        toast.success(editingProducto ? 'Producto actualizado exitosamente' : 'Producto creado exitosamente');
        setIsModalOpen(false);
        setEditingProducto(null);
        fetchProductos();
      } else {
        toast.error(result.message || 'Error al guardar producto');
      }
    } catch (error: any) {
      toast.error(error.message || 'Error de conexión');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Estás seguro de que deseas eliminar este producto? Esta acción desactivará el registro.')) {
      return;
    }
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/productos/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const result = await response.json();
      
      if (result.status === 200 || result.status_code === 200) {
        toast.success('Producto eliminado exitosamente');
        fetchProductos();
      } else {
        toast.error(result.message || 'Error al eliminar producto');
      }
    } catch (error: any) {
      toast.error(error.message || 'Error al eliminar producto');
    }
  };

  const openCreateModal = () => {
    setEditingProducto(null);
    setIsModalOpen(true);
  };

  const openEditModal = (producto: Producto) => {
    setEditingProducto(producto);
    setIsModalOpen(true);
  };

  // Pagination logic
  const totalPages = Math.ceil(total / params.limit);
  const currentPage = Math.floor(params.offset / params.limit) + 1;

  const goToPage = (page: number) => {
    const newOffset = (page - 1) * params.limit;
    setParams(prev => ({ ...prev, offset: newOffset }));
  };

  const updateParams = (newParams: Partial<typeof params>) => {
    setParams(prev => ({ ...prev, ...newParams }));
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
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Gestión de Productos</h1>
          <p className="text-slate-500 text-sm">Administra tu catálogo de productos y servicios.</p>
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
            <Plus className="w-4 h-4" />
            <span className="text-sm">Nuevo Producto</span>
          </button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por código o descripción..."
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
            <span className="text-sm text-slate-500 font-medium">Mostrar inactivos:</span>
            <button
              onClick={() => setShowInactive(!showInactive)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${showInactive ? 'bg-amber-500' : 'bg-slate-300'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${showInactive ? 'translate-x-6' : 'translate-x-1'}`} />
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
                  onClick={() => handleSort('descripcion')}
                >
                  Descripción {getSortIcon('descripcion')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors"
                  onClick={() => handleSort('unidad_medida')}
                >
                  Unidad {getSortIcon('unidad_medida')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors text-right"
                  onClick={() => handleSort('precio_base')}
                >
                  Precio Base {getSortIcon('precio_base')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors text-right"
                  onClick={() => handleSort('existencia')}
                >
                  Existencia {getSortIcon('existencia')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors text-center"
                  onClick={() => handleSort('es_servicio')}
                >
                  Tipo {getSortIcon('es_servicio')}
                </th>
                <th
                  className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider border-r border-slate-100 cursor-pointer hover:text-vortex-primary transition-colors text-center"
                  onClick={() => handleSort('activo')}
                >
                  Estado {getSortIcon('activo')}
                </th>
                <th className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {loading ? (
                <tr className="bg-white">
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="w-8 h-8 border-4 border-slate-200 border-t-vortex-primary rounded-full animate-spin"></div>
                      <p className="text-slate-400 text-sm font-medium">Cargando productos...</p>
                    </div>
                  </td>
                </tr>
              ) : productos.length > 0 ? (
                productos.map((producto) => (
                  <tr key={producto.id} className="hover:bg-vortex-primary/5 transition-colors group even:bg-slate-50/50 odd:bg-white">
                    <td className="px-4 py-2 text-xs font-medium text-slate-700 border-r border-slate-200">{producto.codigo}</td>
                    <td className="px-4 py-2 text-xs font-semibold text-slate-800 border-r border-slate-200">{producto.descripcion}</td>
                    <td className="px-4 py-2 text-xs text-slate-600 border-r border-slate-200">
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase bg-gray-100 text-gray-700">
                        {producto.unidad_medida || 'UND'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs text-right font-semibold text-slate-800 border-r border-slate-200">
                      {new Intl.NumberFormat('es-VE', { style: 'currency', currency: 'VES' }).format(producto.precio_base)}
                    </td>
                    <td className="px-4 py-2 text-xs text-right border-r border-slate-200">
                      <span className={`font-medium ${
                        producto.existencia <= 5 
                          ? 'text-red-600' 
                          : producto.existencia <= 10 
                            ? 'text-amber-600' 
                            : 'text-green-600'
                      }`}>
                        {producto.existencia.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs border-r border-slate-200 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                        producto.es_servicio
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}>
                        {producto.es_servicio ? 'Servicio' : 'Producto'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-xs border-r border-slate-200 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                        producto.activo
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => openEditModal(producto)}
                          className="p-2 text-vortex-primary bg-white border border-slate-200 rounded-lg shadow-sm hover:bg-vortex-primary hover:text-white transition-all active:scale-90"
                          title="Editar"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(producto.id)}
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
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="p-3 bg-slate-100 rounded-full">
                        <Package className="w-6 h-6 text-slate-400" />
                      </div>
                      <p className="text-slate-500 text-sm font-medium">No se encontraron productos</p>
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
            Mostrando <span className="text-slate-800 font-bold">{productos.length}</span> de <span className="text-slate-800 font-bold">{total}</span> registros
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

      <ProductoDrawer
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingProducto(null);
        }}
        onSubmit={handleSaveProducto}
        initialData={editingProducto}
        isEditing={!!editingProducto}
      />
    </div>
  );
};

export default ProductosPage;
