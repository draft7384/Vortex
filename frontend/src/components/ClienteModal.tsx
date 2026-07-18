import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { X, User, MapPin, Phone, Mail, CreditCard, DollarSign, Percent, Building2, AlertCircle } from 'lucide-react';
import type { Cliente } from '../types/api';

const clienteSchema = z.object({
  codigo: z.string().min(1, 'El código es obligatorio'),
  rif: z.string().min(1, 'El RIF es obligatorio'),
  nombre_razon_social: z.string().min(1, 'El nombre es obligatorio'),
  direccion: z.string().nullable(),
  telefono: z.string().nullable(),
  email: z.string().email('Email inválido').nullable().or(z.literal('')),
  condicion_pago: z.enum(['CONTADO', 'CREDITO', 'ANTICIPO']),
  limite_credito: z.number().min(0),
  regimen_iva: z.enum(['ORDINARIO', 'ESPECIAL']),
  es_contribuyente_especial: z.boolean(),
  numero_contribuyente_especial: z.string().nullable(),
  moneda_id: z.number().min(1),
});

type ClienteFormValues = z.infer<typeof clienteSchema>;

interface ClienteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ClienteFormValues) => Promise<void>;
  initialData?: Cliente | null;
}

const ClienteModal: React.FC<ClienteModalProps> = ({ isOpen, onClose, onSubmit, initialData }) => {
  const { register, handleSubmit, reset, setValue, watch, formState: { errors } } = useForm<ClienteFormValues>({
    resolver: zodResolver(clienteSchema),
    defaultValues: {
      codigo: '',
      rif: '',
      nombre_razon_social: '',
      direccion: '',
      telefono: '',
      email: '',
      condicion_pago: 'CONTADO',
      limite_credito: 0,
      regimen_iva: 'ORDINARIO',
      es_contribuyente_especial: false,
      numero_contribuyente_especial: '',
      moneda_id: 1,
    }
  });

  const esContribuyenteEspecial = watch('es_contribuyente_especial');

  useEffect(() => {
    if (initialData) {
      reset({
        ...initialData,
        limite_credito: initialData.limite_credito || 0,
        moneda_id: initialData.moneda_id || 1,
      });
    } else {
      reset({
        codigo: '',
        rif: '',
        nombre_razon_social: '',
        direccion: '',
        telefono: '',
        email: '',
        condicion_pago: 'CONTADO',
        limite_credito: 0,
        regimen_iva: 'ORDINARIO',
        es_contribuyente_especial: false,
        numero_contribuyente_especial: '',
        moneda_id: 1,
      });
    }
  }, [initialData, reset]);

  if (!isOpen) return null;

  const FormField = ({ label, name, error, icon: Icon, children, className = '' }: any) => (
    <div className={`space-y-1.5 ${className}`}>
      <label className="text-xs font-bold text-slate-600 uppercase tracking-wide flex items-center gap-1.5">
        {Icon && <Icon className="w-3.5 h-3.5 text-vortex-primary" />}
        {label}
      </label>
      {children}
      {error && (
        <p className="text-[10px] text-red-500 flex items-center gap-1 mt-0.5">
          <AlertCircle className="w-2.5 h-2.5" />
          {error.message}
        </p>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-3 sm:p-4 animate-[fadeIn_0.2s_ease-out]">
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideInUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl overflow-hidden flex flex-col max-h-[95vh] animate-[slideInUp_0.3s_ease-out]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 sm:px-5 py-3 sm:py-4 bg-gradient-to-r from-vortex-primary to-vortex-secondary flex-shrink-0">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="p-1.5 sm:p-2 bg-white/20 rounded-lg">
              <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-white whitespace-nowrap">
                {initialData ? 'Editar Cliente' : 'Nuevo Cliente'}
              </h3>
              <p className="text-xs sm:text-sm text-white/80 hidden sm:block">
                {initialData ? 'Modifica la información del cliente' : 'Completa los datos para registrar'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 hover:bg-white/20 rounded-full transition-colors group flex-shrink-0"
          >
            <X className="w-5 h-5 text-white group-hover:scale-110 transition-transform" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="overflow-y-auto p-4 sm:p-5 space-y-4 sm:space-y-5 flex-1">
          {/* Sección 1: Información Básica */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-1.5 border-b-2 border-vortex-primary/20">
              <Building2 className="w-3.5 h-3.5" />
              Información Básica
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <FormField label="Código" name="codigo" error={errors.codigo} icon={null}>
                <input
                  {...register('codigo')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="C001"
                />
              </FormField>

              <FormField label="RIF / Cédula" name="rif" error={errors.rif} icon={null}>
                <input
                  {...register('rif')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="J-12345678-9"
                />
              </FormField>

              <FormField label="Moneda" name="moneda_id" error={errors.moneda_id} icon={DollarSign}>
                <select
                  {...register('moneda_id', { valueAsNumber: true })}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value={1}>VES - Bolívares</option>
                  <option value={2}>USD - Dólares</option>
                  <option value={3}>EUR - Euros</option>
                </select>
              </FormField>

              <FormField label="Nombre / Razón Social" name="nombre_razon_social" error={errors.nombre_razon_social} icon={null} className="sm:col-span-2 lg:col-span-1">
                <input
                  {...register('nombre_razon_social')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="Empresa Ejemplo C.A."
                />
              </FormField>
            </div>
          </div>

          {/* Sección 2: Contacto */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-1.5 border-b-2 border-vortex-primary/20">
              <MapPin className="w-3.5 h-3.5" />
              Datos de Contacto
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <FormField label="Dirección" name="direccion" error={errors.direccion} icon={MapPin} className="sm:col-span-2 lg:col-span-4">
                <textarea
                  {...register('direccion')}
                  rows={1}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 resize-none"
                  placeholder="Av. Principal, Edificio Torre Vortex, Piso 5..."
                />
              </FormField>

              <FormField label="Teléfono" name="telefono" error={errors.telefono} icon={Phone}>
                <input
                  {...register('telefono')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="0212-5551234"
                />
              </FormField>

              <FormField label="Email" name="email" error={errors.email} icon={Mail}>
                <input
                  {...register('email')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="contacto@empresa.com"
                />
              </FormField>
            </div>
          </div>

          {/* Sección 3: Condiciones Comerciales */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-1.5 border-b-2 border-vortex-primary/20">
              <CreditCard className="w-3.5 h-3.5" />
              Condiciones Comerciales
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <FormField label="Condición de Pago" name="condicion_pago" error={errors.condicion_pago} icon={CreditCard}>
                <select
                  {...register('condicion_pago')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value="CONTADO">Contado</option>
                  <option value="CREDITO">Crédito</option>
                  <option value="ANTICIPO">Anticipo</option>
                </select>
              </FormField>

              <FormField label="Límite de Crédito" name="limite_credito" error={errors.limite_credito} icon={DollarSign}>
                <input
                  type="number"
                  {...register('limite_credito', { valueAsNumber: true })}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 disabled:bg-slate-100"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                />
              </FormField>

              <FormField label="Régimen IVA" name="regimen_iva" error={errors.regimen_iva} icon={Percent}>
                <select
                  {...register('regimen_iva')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value="ORDINARIO">Ordinario</option>
                  <option value="ESPECIAL">Especial</option>
                </select>
              </FormField>
            </div>
          </div>

          {/* Sección 4: Datos Fiscales */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-vortex-primary uppercase tracking-wider flex items-center gap-2 pb-1.5 border-b-2 border-vortex-primary/20">
              <Building2 className="w-3.5 h-3.5" />
              Datos Fiscales
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div className="flex items-center space-x-2 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <input
                  type="checkbox"
                  {...register('es_contribuyente_especial')}
                  className="w-4 h-4 text-vortex-primary rounded border-slate-300 focus:ring-vortex-primary cursor-pointer"
                />
                <label className="text-xs font-bold text-slate-700 uppercase cursor-pointer select-none">
                  Contribuyente Especial
                </label>
              </div>

              {esContribuyenteEspecial && (
                <FormField 
                  label="N° Contribuyente" 
                  name="numero_contribuyente_especial" 
                  error={errors.numero_contribuyente_especial}
                  icon={Building2}
                >
                  <input
                    {...register('numero_contribuyente_especial')}
                    className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 animate-[fadeIn_0.2s_ease-out]"
                    placeholder="00001234567"
                  />
                </FormField>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-4 border-t border-slate-200 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 text-xs font-bold text-white bg-gradient-to-r from-vortex-primary to-vortex-secondary hover:from-vortex-secondary hover:to-vortex-primary rounded-lg transition-all shadow-lg shadow-vortex-primary/30 active:scale-95"
            >
              {initialData ? 'Guardar Cambios' : 'Crear Cliente'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ClienteModal;
