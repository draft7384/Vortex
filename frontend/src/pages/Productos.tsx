/**
 * Pagina de Gestion de Productos
 * Diseño moderno con panel lateral deslizante
 */

import React, { useState, useEffect } from 'react';
import { 
  Package, Plus, Search, Edit, Trash2, Download, Upload, 
  AlertTriangle, CheckCircle, Eye, EyeOff 
} from 'lucide-react';
import ProductoModal from '../components/ProductoModal';

interface Producto {
  id: number;
  codigo: string;
  descripcion: string;
  precio_base: number;
  impuesto_pct: number;
  existencia: number;
  es_servicio: boolean;
  activo: boolean;
}

const Productos: React.FC = () => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProducto, setEditingProducto] = useState<Producto | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  // Cargar productos
  useEffect(() => {
    fetchProductos();
  }, []);

  const fetchProductos = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/productos/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      if (data.status === 200) {
        setProductos(data.data.items || []);
      }
    } catch (error) {
      console.error('Error al cargar productos:', error);
    } finally {
      setLoading(false);
    }
  };

  // Crear/Actualizar producto
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
      
      if (result.status === 200 || result.status === 201) {
        fetchProductos();
        setIsModalOpen(false);
        setEditingProducto(null);
        
        // Mostrar toast de exito
        alert(result.message || 'Producto guardado exitosamente');
      } else {
        alert(result.message || 'Error al guardar producto');
      }
    } catch (error) {
      console.error('Error al guardar:', error);
      alert('Error de conexion');
    }
  };

  // Editar producto
  const handleEdit = (producto: Producto) => {
    setEditingProducto(producto);
    setIsModalOpen(true);
  };

  // Eliminar/Desactivar producto
  const handleDelete = async (id: number) => {
    if (!confirm('¿Esta seguro de desactivar este producto?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/productos/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const result = await response.json();
      
      if (result.status === 200) {
        fetchProductos();
        alert('Producto desactivado exitosamente');
      } else {
        alert(result.message || 'Error al desactivar');
      }
    } catch (error) {
      console.error('Error al eliminar:', error);
      alert('Error de conexion');
    }
  };

  // Importar Excel
  const handleImportExcel = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx')) {
      alert('Solo se permiten archivos .xlsx');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/productos/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();
      
      if (result.status === 200) {
        fetchProductos();
        const { exitosos, fallidos } = result.data;
        alert(`Importacion completada:\n✅ ${exitosos} exitosos\n❌ ${fallidos} fallidos`);
      } else {
        alert(result.message || 'Error al importar');
      }
    } catch (error) {
      console.error('Error al importar:', error);
      alert('Error de conexion');
    }

    // Reset input
    event.target.value = '';
  };

  // Descargar plantilla
  const handleDownloadTemplate = () => {
    const link = document.createElement('a');
    link.href = '/plantilla_productos.xlsx';
    link.download = 'plantilla_productos.xlsx';
    link.click();
  };

  // Filtrar productos
  const filteredProductos = productos.filter(p => {
    const matchesSearch = 
      p.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.descripcion.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = showInactive ? true : p.activo;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Productos</h1>
        <p className="text-gray-600">Gestiona tu catalogo de productos y servicios</p>
      </div>

      {/* Toolbar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          {/* Buscador */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por codigo o descripcion..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent"
            />
          </div>

          {/* Acciones */}
          <div className="flex flex-wrap gap-3">
            {/* Toggle Activos/Inactivos */}
            <button
              onClick={() => setShowInactive(!showInactive)}
              className={`px-4 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 ${
                showInactive 
                  ? 'bg-amber-100 text-amber-700 border-2 border-amber-300' 
                  : 'bg-gray-100 text-gray-700 border-2 border-gray-300'
              }`}
            >
              {showInactive ? <Eye size={18} /> : <EyeOff size={18} />}
              {showInactive ? 'Ver Activos' : 'Ver Inactivos'}
            </button>

            {/* Importar Excel */}
            <label className="px-4 py-2.5 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 cursor-pointer transition-all flex items-center gap-2">
              <Upload size={18} />
              Importar Excel
              <input
                type="file"
                accept=".xlsx"
                onChange={handleImportExcel}
                className="hidden"
              />
            </label>

            {/* Descargar Plantilla */}
            <button
              onClick={handleDownloadTemplate}
              className="px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-all flex items-center gap-2"
            >
              <Download size={18} />
              Plantilla
            </button>

            {/* Nuevo Producto */}
            <button
              onClick={() => {
                setEditingProducto(null);
                setIsModalOpen(true);
              }}
              className="px-4 py-2.5 bg-gradient-to-r from-vortex-primary to-vortex-secondary text-white rounded-lg font-medium hover:from-vortex-secondary hover:to-vortex-primary transition-all flex items-center gap-2 shadow-md"
            >
              <Plus size={18} />
              Nuevo Producto
            </button>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-vortex-primary to-vortex-secondary text-white">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Codigo</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Descripcion</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Unidad</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider">Precio Base</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider">IVA %</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider">Existencia</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider">Tipo</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider">Estado</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center">
                    <div className="flex items-center justify-center gap-3 text-gray-500">
                      <div className="w-5 h-5 border-2 border-vortex-primary border-t-transparent rounded-full animate-spin" />
                      Cargando productos...
                    </div>
                  </td>
                </tr>
              ) : filteredProductos.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center">
                    <div className="flex flex-col items-center gap-3 text-gray-500">
                      <Package size={40} className="text-gray-300" />
                      <p className="text-sm">No se encontraron productos</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredProductos.map((producto) => (
                  <tr 
                    key={producto.id} 
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs font-medium text-gray-900">
                        {producto.codigo}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-700">{producto.descripcion}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                        {producto.unidad_medida || 'UND'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-xs font-semibold text-gray-900">
                        ${producto.precio_base.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-xs text-gray-600">{producto.impuesto_pct}%</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className={`text-xs font-medium ${
                        producto.existencia <= 5 
                          ? 'text-red-600' 
                          : producto.existencia <= 10 
                            ? 'text-amber-600' 
                            : 'text-green-600'
                      }`}>
                        {producto.existencia.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        producto.es_servicio
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}>
                        {producto.es_servicio ? 'Servicio' : 'Producto'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        producto.activo
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          onClick={() => handleEdit(producto)}
                          className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                          title="Editar"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(producto.id)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                          title="Desactivar"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Panel Lateral */}
      <ProductoModal
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

export default Productos;
