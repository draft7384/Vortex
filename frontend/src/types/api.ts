export type Cliente = {
  id: number;
  codigo: string;
  rif: string;
  nombre_razon_social: string;
  direccion: string | null;
  telefono: string | null;
  email: string | null;
  condicion_pago: 'CONTADO' | 'CREDITO' | 'ANTICIPO';
  limite_credito: number;
  regimen_iva: 'ORDINARIO' | 'ESPECIAL';
  es_contribuyente_especial: boolean;
  numero_contribuyente_especial: string | null;
  moneda_id: number;
  activo: boolean;
  creado_en: string;
};

export type APIResponse<T> = {
  status_code: number;
  message: string;
  data: T;
};

export type PagedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
