/**
 * Panel lateral deslizante para CRUD de Productos
 * Diseño moderno idéntico a Clientes con animación slide-in
 */

import React, { useState, useEffect } from 'react';
import { X, Package, Save, AlertCircle, CheckCircle, DollarSign, Percent } from 'lucide-react';

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
      newErrors.codigo = 'Código requerido';
    } else if (formData.codigo.length > 30) {
      newErrors.codigo = 'Máximo 30 caracteres';
    }

    if (!formData.descripcion.trim()) {
      newErrors.descripcion = 'Descripción requerida';
    } else if (formData.descripcion.length > 255) {
      newErrors.descripcion = 'Máximo 255 caracteres';
    }

    if (!formData.precio_base || parseFloat(formData.precio_base) < 0) {
      newErrors.precio_base = 'Precio válido requerido';
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

  const FormField = ({ label, name, error, icon: Icon, children, className = '' }: any) => (
    <div className={`space-y-1.5 ${className}`}>
      <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
        {Icon && <Icon className="w-3 h-3 text-vortex-primary" />}
        {label}
      </label>
      {children}
      {error && (
        <p className="text-[9px] text-red-500 flex items-center gap-1 mt-0.5">
          <AlertCircle className="w-2 h-2" />
          {error.message}
        </p>
      )}
    </div>
  );

  return (
    <>
      {/* Overlay */}
      <div 
        className={`fixed inset-0 z-[99] bg-black/60 backdrop-blur-sm transition-opacity duration-300 ease-in-out ${
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />
      
      {/* Drawer Panel */}
      <div className={`fixed top-0 right-0 h-full w-full max-w-2xl bg-white shadow-2xl z-[100] transform transition-transform duration-300 ease-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-vortex-primary to-vortex-secondary flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Package className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white whitespace-nowrap">
                {isEditing ? 'Editar Producto' : 'Nuevo Producto'}
              </h3>
              <p className="text-xs text-white/80">
                {isEditing ? 'Modifica la información' : 'Completa los datos para registrar'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-white/20 rounded-full transition-colors group flex-shrink-0"
          >
            <X className="w-5 h-5 text-white group-hover:scale-110 transition-transform" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="overflow-y-auto h-[calc(100vh-80px)] p-5 space-y-4">
          {/* Sección 1: Información Básica */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-2 border-b-2 border-vortex-primary/20">
              <Package className="w-3.5 h-3.5" />
              Información del Producto
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Código" name="codigo" error={errors.codigo} icon={null}>
                <input
                  type="text"
                  value={formData.codigo}
                  onChange={(e) => handleChange('codigo', e.target.value)}
                  className={`w-full px-2.5 py-2 text-xs border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 ${
                    errors.codigo ? 'border-red-500 bg-red-50' : 'border-slate-300'
                  }`}
                  placeholder="PROD001"
                />
              </FormField>

              <FormField label="Unidad de Medida" name="unidad_medida" icon={Package}>
                <select
                  value={formData.unidad_medida}
                  onChange={(e) => handleChange('unidad_medida', e.target.value)}
                  className="w-full px-2.5 py-2 text-xs border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
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
              </FormField>

              <FormField label="Descripción" name="descripcion" error={errors.descripcion} icon={null} className="col-span-2">
                <textarea
                  value={formData.descripcion}
                  onChange={(e) => handleChange('descripcion', e.target.value)}
                  rows={2}
                  className={`w-full px-2.5 py-2 text-xs border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 resize-none ${
                    errors.descripcion ? 'border-red-500 bg-red-50' : 'border-slate-300'
                  }`}
                  placeholder="Descripción detallada del producto o servicio"
                />
              </FormField>
            </div>
          </div>

          {/* Sección 2: Precios e Impuestos */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-2 border-b-2 border-vortex-primary/20">
              <DollarSign className="w-3.5 h-3.5" />
              Precios e Impuestos
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Precio Base" name="precio_base" error={errors.precio_base} icon={DollarSign}>
                <div className="relative">
                  <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500 text-xs">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.precio_base}
                    onChange={(e) => handleChange('precio_base', e.target.value)}
                    className={`w-full pl-6 pr-2.5 py-2 text-xs border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 ${
                      errors.precio_base ? 'border-red-500 bg-red-50' : 'border-slate-300'
                    }`}
                    placeholder="0.00"
                  />
                </div>
              </FormField>

              <FormField label="IVA (%)" name="impuesto_pct" error={errors.impuesto_pct} icon={Percent}>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.impuesto_pct}
                  onChange={(e) => handleChange('impuesto_pct', parseFloat(e.target.value))}
                  className={`w-full px-2.5 py-2 text-xs border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 ${
                    errors.impuesto_pct ? 'border-red-500 bg-red-50' : 'border-slate-300'
                  }`}
                />
              </FormField>
            </div>
          </div>

          {/* Sección 3: Inventario */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-2 border-b-2 border-vortex-primary/20">
              <CheckCircle className="w-3.5 h-3.5" />
              Inventario
            </h4>
            <div className="space-y-3">
              <FormField label="Existencia Inicial" name="existencia" error={errors.existencia} icon={Package}>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.existencia}
                  onChange={(e) => handleChange('existencia', parseFloat(e.target.value))}
                  className={`w-full px-2.5 py-2 text-xs border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 ${
                    errors.existencia ? 'border-red-500 bg-red-50' : 'border-slate-300'
                  }`}
                />
              </FormField>

              <div className="flex items-center space-x-2 p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <input
                  type="checkbox"
                  id="es_servicio"
                  checked={formData.es_servicio}
                  onChange={(e) => handleChange('es_servicio', e.target.checked)}
                  className="w-3.5 h-3.5 text-vortex-primary rounded border-slate-300 focus:ring-vortex-primary cursor-pointer"
                />
                <label htmlFor="es_servicio" className="text-[10px] font-bold text-slate-700 uppercase cursor-pointer select-none">
                  Es un servicio (no controla inventario)
                </label>
              </div>
              
              {formData.es_servicio && (
                <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
                  ℹ️ No se descontará existencias al facturar este producto.
                </p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-200 mt-4 sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 text-xs font-bold text-white bg-gradient-to-r from-vortex-primary to-vortex-secondary hover:from-vortex-secondary hover:to-vortex-primary rounded-lg transition-all shadow-lg shadow-vortex-primary/30 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  {isEditing ? 'Guardar Cambios' : 'Crear Producto'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </>
  );
};

export default ProductoModal;
