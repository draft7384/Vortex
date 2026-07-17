import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { X } from 'lucide-react';
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
  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm<ClienteFormValues>({
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50">
          <h3 className="text-lg font-bold text-slate-800">
            {initialData ? 'Editar Cliente' : 'Nuevo Cliente'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-200 rounded-full transition-colors">
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="overflow-y-auto p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Código */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Código</label>
              <input
                {...register('codigo')}
                className={`w-full px-3 py-2 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary ${errors.codigo ? 'border-red-500 ring-red-100' : 'border-slate-300 focus:border-vortex-primary'}`}
                placeholder="C001"
              />
              {errors.codigo && <p className="text-xs text-red-500">{errors.codigo.message}</p>}
            </div>

            {/* RIF */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">RIF / Cédula</label>
              <input
                {...register('rif')}
                className={`w-full px-3 py-2 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary ${errors.rif ? 'border-red-500 ring-red-100' : 'border-slate-300 focus:border-vortex-primary'}`}
                placeholder="J-12345678-9"
              />
              {errors.rif && <p className="text-xs text-red-500">{errors.rif.message}</p>}
            </div>

            {/* Nombre */}
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-semibold text-slate-700">Nombre o Razón Social</label>
              <input
                {...register('nombre_razon_social')}
                className={`w-full px-3 py-2 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary ${errors.nombre_razon_social ? 'border-red-500 ring-red-100' : 'border-slate-300 focus:border-vortex-primary'}`}
                placeholder="Empresa Ejemplo C.A."
              />
              {errors.nombre_razon_social && <p className="text-xs text-red-500">{errors.nombre_razon_social.message}</p>}
            </div>

            {/* Dirección */}
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-semibold text-slate-700">Dirección</label>
              <textarea
                {...register('direccion')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary"
                rows={2}
              />
            </div>

            {/* Teléfono */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Teléfono</label>
              <input
                {...register('telefono')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary focus:border-vortex-primary"
              />
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Email</label>
              <input
                {...register('email')}
                className={`w-full px-3 py-2 border rounded-lg outline-none transition-all focus:ring-2 focus:ring-vortex-primary ${errors.email ? 'border-red-500 ring-red-100' : 'border-slate-300 focus:border-vortex-primary'}`}
              />
              {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
            </div>

            {/* Condición de Pago */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Condición de Pago</label>
              <select
                {...register('condicion_pago')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary"
              >
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
                <option value="ANTICIPO">Anticipo</option>
              </select>
            </div>

            {/* Límite de Crédito */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Límite de Crédito (VES)</label>
              <input
                type="number"
                {...register('limite_credito', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary"
              />
            </div>

            {/* Régimen IVA */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Régimen IVA</label>
              <select
                {...register('regimen_iva')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary"
              >
                <option value="ORDINARIO">Ordinario</option>
                <option value="ESPECIAL">Especial</option>
              </select>
            </div>

            {/* Moneda ID (Simplificado) */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Moneda Preferida ID</label>
              <input
                type="number"
                {...register('moneda_id', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary"
              />
            </div>

            {/* Contribuyente Especial */}
            <div className="flex items-center space-x-3 pt-6">
              <input
                type="checkbox"
                {...register('es_contribuyente_especial')}
                className="w-5 h-5 text-vortex-primary rounded border-slate-300 focus:ring-vortex-primary"
              />
              <label className="text-sm font-semibold text-slate-700">Contribuyente Especial</label>
            </div>

            {/* Número Contribuyente Especial */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-700">Nro. Contribuyente Especial</label>
              <input
                {...register('numero_contribuyente_especial')}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-vortex-primary"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-6 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-6 py-2 text-sm font-bold text-white bg-vortex-primary hover:bg-vortex-secondary rounded-lg transition-colors shadow-md shadow-vortex-primary/20"
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
