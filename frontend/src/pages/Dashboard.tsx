import React from 'react';
import { TrendingUp, Users, Package, FileText } from 'lucide-react';

const KPICard = ({ title, value, trend, icon: Icon, color }: any) => (
  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between transition-all hover:shadow-md">
    <div className="flex-1">
      <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
      <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
      <span className={`text-xs font-bold ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}% vs mes pasado
      </span>
    </div>
    <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center text-white shadow-lg`}>
      <Icon size={24} />
    </div>
  </div>
);

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex flex-col">
        <h1 className="text-3xl font-bold text-slate-800">Panel de Control</h1>
        <p className="text-slate-500">Bienvenido de vuelta. Aquí tienes el resumen de tu negocio hoy.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Ventas del Día"
          value="$12,450.00"
          trend={12}
          icon={TrendingUp}
          color="bg-blue-500"
        />
        <KPICard
          title="Deuda Pendiente"
          value="$4,120.50"
          trend={-2}
          icon={FileText}
          color="bg-orange-500"
        />
        <KPICard
          title="Clientes Activos"
          value="142"
          trend={5}
          icon={Users}
          color="bg-emerald-500"
        />
        <KPICard
          title="Bajo Stock"
          value="12 prod."
          trend={0}
          icon={Package}
          color="bg-rose-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-slate-800">Actividad Reciente</h3>
            <button className="text-sm text-vortex-primary hover:underline font-medium">Ver todo</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-100">
                  <th className="pb-3 font-medium">Documento</th>
                  <th className="pb-3 font-medium">Cliente</th>
                  <th className="pb-3 font-medium">Fecha</th>
                  <th className="pb-3 font-medium text-right">Total</th>
                  <th className="pb-3 font-medium text-center">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {[
                  { cod: 'FAC-00012', cli: 'Cliente Credito C.A.', date: '2026-07-15', tot: '$1,160.00', status: 'EMITIDO', statusColor: 'bg-blue-100 text-blue-600' },
                  { cod: 'FAC-00010', cli: 'Ana Martinez', date: '2026-07-14', tot: '$58.00', status: 'PAGADO', statusColor: 'bg-green-100 text-green-600' },
                  { cod: 'FAC-00008', cli: 'Luis Rodriguez', date: '2026-07-13', tot: '$6.38', status: 'EMITIDO', statusColor: 'bg-blue-100 text-blue-600' },
                  { cod: 'FAC-00011', cli: 'Jose Perez', date: '2026-07-12', tot: '$116.00', status: 'ANULADO', statusColor: 'bg-red-100 text-red-600' },
                ].map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 font-medium text-slate-700">{row.cod}</td>
                    <td className="py-3 text-slate-500">{row.cli}</td>
                    <td className="py-3 text-slate-500">{row.date}</td>
                    <td className="py-3 text-right font-semibold text-slate-700">{row.tot}</td>
                    <td className="py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${row.statusColor}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Acciones Rápidas</h3>
          <div className="grid grid-cols-1 gap-3">
            <button className="flex items-center space-x-3 p-3 rounded-xl bg-slate-50 hover:bg-vortex-primary/10 hover:text-vortex-primary transition-all group text-left font-medium text-slate-600">
              <div className="p-2 rounded-lg bg-white shadow-sm group-hover:bg-white"><FileText size={18} /></div>
              <span className="text-sm">Emitir Factura</span>
            </button>
            <button className="flex items-center space-x-3 p-3 rounded-xl bg-slate-50 hover:bg-vortex-primary/10 hover:text-vortex-primary transition-all group text-left font-medium text-slate-600">
              <div className="p-2 rounded-lg bg-white shadow-sm group-hover:bg-white"><Users size={18} /></div>
              <span className="text-sm">Nuevo Cliente</span>
            </button>
            <button className="flex items-center space-x-3 p-3 rounded-xl bg-slate-50 hover:bg-vortex-primary/10 hover:text-vortex-primary transition-all group text-left font-medium text-slate-600">
              <div className="p-2 rounded-lg bg-white shadow-sm group-hover:bg-white"><Package size={18} /></div>
              <span className="text-sm">Cargar Producto</span>
            </button>
            <button className="flex items-center space-x-3 p-3 rounded-xl bg-slate-50 hover:bg-vortex-primary/10 hover:text-vortex-primary transition-all group text-left font-medium text-slate-600">
              <div className="p-2 rounded-lg bg-white shadow-sm group-hover:bg-white"><TrendingUp size={18} /></div>
              <span className="text-sm">Ver Estado de Cuenta</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
