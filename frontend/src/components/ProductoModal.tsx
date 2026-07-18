/**
 * Panel lateral deslizante para CRUD de Productos
 * Diseño moderno con animacion slide-in desde la derecha
 */

import React, { useState, useEffect } from 'react';
import { X, Package, Save, AlertCircle, CheckCircle } from 'lucide-react';

interface ProductoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  initialData?: any;
  isEditing?: boolean;
}

const ProductoModal: React.FC<ProductoModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  isEditing = false,
}) => {
  const [formData, setFormData] = useState({
    codigo: '',
    descripcion: '',
    unidad_medida: 'UND',
    precio_base: '',
    impuesto_pct: 16.0,
    existencia: 0,
    es_servicio: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialData && isEditing) {
      setFormData({
        codigo: initialData.codigo || '',
        descripcion: initialData.descripcion || '',
        unidad_medida: initialData.unidad_medida || 'UND',
        precio_base: initialData.precio_base?.toString() || '',
        impuesto_pct: initialData.impuesto_pct || 16.0,
        existencia: initialData.existencia || 0,
        es_servicio: initialData.es_servicio || false,
      });
    } else {
      resetForm();
    }
  }, [initialData, isEditing, isOpen]);

  const resetForm = () => {
    setFormData({
      codigo: '',
      descripcion: '',
      unidad_medida: 'UND',
      precio_base: '',
      impuesto_pct: 16.0,
      existencia: 0,
      es_servicio: false,
    });
    setErrors({});
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.codigo.trim()) {
      newErrors.codigo = 'Codigo requerido';
    } else if (formData.codigo.length > 30) {
      newErrors.codigo = 'Maximo 30 caracteres';
    }

    if (!formData.descripcion.trim()) {
      newErrors.descripcion = 'Descripcion requerida';
    } else if (formData.descripcion.length > 255) {
      newErrors.descripcion = 'Maximo 255 caracteres';
    }

    if (!formData.precio_base || parseFloat(formData.precio_base) < 0) {
      newErrors.precio_base = 'Precio valido requerido';
    }

    if (formData.impuesto_pct < 0 || formData.impuesto_pct > 100) {
      newErrors.impuesto_pct = 'IVA entre 0 y 100';
    }

    if (formData.existencia < 0) {
      newErrors.existencia = 'No puede ser negativo';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        ...formData,
        precio_base: parseFloat(formData.precio_base),
        existencia: parseFloat(formData.existencia.toString()),
      });
      resetForm();
      onClose();
    } catch (error) {
      console.error('Error al guardar:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity duration-300 ease-in-out"
        onClick={onClose}
      />
      
      {/* Panel Deslizante */}
      <div className={`
        fixed top-0 right-0 h-full w-full max-w-md 
        bg-gradient-to-b from-white to-gray-50 
        shadow-2xl z-50 transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        {/* Header */}
        <div className="bg-gradient-to-r from-vortex-primary to-vortex-secondary p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                <Package size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold">
                  {isEditing ? 'Editar Producto' : 'Nuevo Producto'}
                </h2>
                <p className="text-sm text-white/80">
                  {isEditing ? 'Actualiza la informacion' : 'Registra un nuevo producto o servicio'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors duration-200"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="p-5 h-[calc(100vh-140px)] overflow-y-auto">
          <div className="space-y-5">
            {/* Seccion 1: Informacion Basica */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <Package size={18} className="text-vortex-primary" />
                <h3 className="font-semibold text-gray-800">Informacion del Producto</h3>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Codigo <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.codigo}
                    onChange={(e) => handleChange('codigo', e.target.value)}
                    className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all ${
                      errors.codigo ? 'border-red-500 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="Ej: PROD001"
                  />
                  {errors.codigo && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> {errors.codigo}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Descripcion <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={formData.descripcion}
                    onChange={(e) => handleChange('descripcion', e.target.value)}
                    rows={2}
                    className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all resize-none ${
                      errors.descripcion ? 'border-red-500 bg-red-50' : 'border-gray-300'
                    }`}
                    placeholder="Descripcion detallada del producto"
                  />
                  {errors.descripcion && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> {errors.descripcion}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Unidad de Medida
                  </label>
                  <select
                    value={formData.unidad_medida}
                    onChange={(e) => handleChange('unidad_medida', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all"
                  >
                    <option value="UND">Unidades (UND)</option>
                    <option value="HRS">Horas (HRS)</option>
                    <option value="KG">Kilogramos (KG)</option>
                    <option value="LTS">Litros (LTS)</option>
                    <option value="MTR">Metros (MTR)</option>
                    <option value="CAJ">Cajas (CAJ)</option>
                    <option value="PQT">Paquetes (PQT)</option>
                    <option value="OTR">Otro</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Seccion 2: Precios e Impuestos */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle size={18} className="text-vortex-primary" />
                <h3 className="font-semibold text-gray-800">Precios e Impuestos</h3>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Precio Base <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.precio_base}
                      onChange={(e) => handleChange('precio_base', e.target.value)}
                      className={`w-full pl-7 pr-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all ${
                        errors.precio_base ? 'border-red-500 bg-red-50' : 'border-gray-300'
                      }`}
                      placeholder="0.00"
                    />
                  </div>
                  {errors.precio_base && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> {errors.precio_base}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    IVA (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={formData.impuesto_pct}
                    onChange={(e) => handleChange('impuesto_pct', parseFloat(e.target.value))}
                    className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all ${
                      errors.impuesto_pct ? 'border-red-500 bg-red-50' : 'border-gray-300'
                    }`}
                  />
                  {errors.impuesto_pct && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> {errors.impuesto_pct}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Seccion 3: Inventario */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center gap-2 mb-3">
                <Package size={18} className="text-vortex-primary" />
                <h3 className="font-semibold text-gray-800">Inventario</h3>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Existencia Inicial
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.existencia}
                    onChange={(e) => handleChange('existencia', parseFloat(e.target.value))}
                    className={`w-full px-3 py-2 text-sm border rounded-lg focus:ring-2 focus:ring-vortex-primary focus:border-transparent transition-all ${
                      errors.existencia ? 'border-red-500 bg-red-50' : 'border-gray-300'
                    }`}
                  />
                  {errors.existencia && (
                    <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle size={12} /> {errors.existencia}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="es_servicio"
                    checked={formData.es_servicio}
                    onChange={(e) => handleChange('es_servicio', e.target.checked)}
                    className="w-4 h-4 text-vortex-primary rounded focus:ring-vortex-primary"
                  />
                  <label htmlFor="es_servicio" className="text-sm text-gray-700 cursor-pointer select-none">
                    Es un servicio (no controla inventario)
                  </label>
                </div>
                
                {formData.es_servicio && (
                  <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
                    ℹ️ Al marcar esta opcion, el sistema no descontara existencias al facturar este item.
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Botones */}
          <div className="mt-6 space-y-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 bg-gradient-to-r from-vortex-primary to-vortex-secondary 
                       text-white font-semibold rounded-xl shadow-lg 
                       hover:from-vortex-secondary hover:to-vortex-primary 
                       active:scale-[0.98] transition-all duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save size={18} />
                  {isEditing ? 'Actualizar Producto' : 'Crear Producto'}
                </>
              )}
            </button>
            
            <button
              type="button"
              onClick={onClose}
              className="w-full py-3 px-4 bg-white text-gray-700 font-semibold rounded-xl border-2 border-gray-300
                       hover:bg-gray-50 active:scale-[0.98] transition-all duration-200"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default ProductoModal;
