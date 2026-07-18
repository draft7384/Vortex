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

  const FormField = ({ label, name, error, icon: Icon, children }: any) => (
    <div className="space-y-2">
      <label className="text-sm font-semibold text-slate-700 flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-vortex-primary" />}
        {label}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error.message}
        </p>
      )}
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh] animate-in slide-in-from-bottom-4 duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 bg-gradient-to-r from-vortex-primary to-vortex-secondary">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">
                {initialData ? 'Editar Cliente' : 'Nuevo Cliente'}
              </h3>
              <p className="text-sm text-white/80">
                {initialData ? 'Modifica la información del cliente' : 'Completa los datos para registrar un nuevo cliente'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-white/20 rounded-full transition-colors group"
          >
            <X className="w-5 h-5 text-white group-hover:scale-110 transition-transform" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="overflow-y-auto p-6 space-y-8">
          {/* Sección 1: Información Básica */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2 pb-2 border-b border-slate-200">
              <Building2 className="w-4 h-4 text-vortex-primary" />
              Información Básica
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <FormField label="Código" name="codigo" error={errors.codigo} icon={null}>
                <input
                  {...register('codigo')}
                  className={`w-full px-4 py-2.5 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary ${
                    errors.codigo ? 'border-red-500 ring-red-100 bg-red-50' : 'border-slate-300 bg-white hover:border-vortex-primary/50'
                  }`}
                  placeholder="C001"
                />
              </FormField>

              <FormField label="RIF / Cédula" name="rif" error={errors.rif} icon={null}>
                <input
                  {...register('rif')}
                  className={`w-full px-4 py-2.5 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary ${
                    errors.rif ? 'border-red-500 ring-red-100 bg-red-50' : 'border-slate-300 bg-white hover:border-vortex-primary/50'
                  }`}
                  placeholder="J-12345678-9"
                />
              </FormField>

              <FormField label="Moneda Preferida" name="moneda_id" error={errors.moneda_id} icon={DollarSign}>
                <select
                  {...register('moneda_id', { valueAsNumber: true })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value={1}>VES - Bolívares</option>
                  <option value={2}>USD - Dólares</option>
                  <option value={3}>EUR - Euros</option>
                </select>
              </FormField>

              <FormField label="Nombre o Razón Social" name="nombre_razon_social" error={errors.nombre_razon_social} icon={null}>
                <input
                  {...register('nombre_razon_social')}
                  className={`w-full md:col-span-2 px-4 py-2.5 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary ${
                    errors.nombre_razon_social ? 'border-red-500 ring-red-100 bg-red-50' : 'border-slate-300 bg-white hover:border-vortex-primary/50'
                  }`}
                  placeholder="Empresa Ejemplo C.A."
                />
              </FormField>
            </div>
          </div>

          {/* Sección 2: Contacto */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2 pb-2 border-b border-slate-200">
              <MapPin className="w-4 h-4 text-vortex-primary" />
              Datos de Contacto
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <FormField label="Dirección" name="direccion" error={errors.direccion} icon={MapPin}>
                <textarea
                  {...register('direccion')}
                  rows={2}
                  className="w-full md:col-span-3 px-4 py-2.5 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 resize-none"
                  placeholder="Av. Principal, Edificio Torre Vortex, Piso 5..."
                />
              </FormField>

              <FormField label="Teléfono" name="telefono" error={errors.telefono} icon={Phone}>
                <input
                  {...register('telefono')}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50"
                  placeholder="0212-5551234"
                />
              </FormField>

              <FormField label="Email" name="email" error={errors.email} icon={Mail}>
                <input
                  {...register('email')}
                  className={`w-full px-4 py-2.5 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary ${
                    errors.email ? 'border-red-500 ring-red-100 bg-red-50' : 'border-slate-300 bg-white hover:border-vortex-primary/50'
                  }`}
                  placeholder="contacto@empresa.com"
                />
              </FormField>
            </div>
          </div>

          {/* Sección 3: Condiciones Comerciales */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2 pb-2 border-b border-slate-200">
              <CreditCard className="w-4 h-4 text-vortex-primary" />
              Condiciones Comerciales
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <FormField label="Condición de Pago" name="condicion_pago" error={errors.condicion_pago} icon={CreditCard}>
                <select
                  {...register('condicion_pago')}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value="CONTADO">Contado</option>
                  <option value="CREDITO">Crédito</option>
                  <option value="ANTICIPO">Anticipo</option>
                </select>
              </FormField>

              <FormField label="Límite de Crédito (VES)" name="limite_credito" error={errors.limite_credito} icon={DollarSign}>
                <input
                  type="number"
                  {...register('limite_credito', { valueAsNumber: true })}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                />
              </FormField>

              <FormField label="Régimen IVA" name="regimen_iva" error={errors.regimen_iva} icon={Percent}>
                <select
                  {...register('regimen_iva')}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 transition-all"
                >
                  <option value="ORDINARIO">Ordinario</option>
                  <option value="ESPECIAL">Especial</option>
                </select>
              </FormField>
            </div>
          </div>

          {/* Sección 4: Datos Fiscales */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2 pb-2 border-b border-slate-200">
              <Building2 className="w-4 h-4 text-vortex-primary" />
              Datos Fiscales
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="flex items-center space-x-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <input
                  type="checkbox"
                  {...register('es_contribuyente_especial')}
                  className="w-5 h-5 text-vortex-primary rounded border-slate-300 focus:ring-vortex-primary cursor-pointer"
                />
                <label className="text-sm font-semibold text-slate-700 cursor-pointer select-none flex-1">
                  Contribuyente Especial
                </label>
              </div>

              {esContribuyenteEspecial && (
                <FormField 
                  label="Número de Contribuyente Especial" 
                  name="numero_contribuyente_especial" 
                  error={errors.numero_contribuyente_especial}
                  icon={Building2}
                >
                  <input
                    {...register('numero_contribuyente_especial')}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary bg-white hover:border-vortex-primary/50 animate-in slide-in-from-left-2"
                    placeholder="00001234567"
                  />
                </FormField>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors border border-slate-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-8 py-2.5 text-sm font-bold text-white bg-gradient-to-r from-vortex-primary to-vortex-secondary hover:from-vortex-secondary hover:to-vortex-primary rounded-lg transition-all shadow-lg shadow-vortex-primary/30 active:scale-95"
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
