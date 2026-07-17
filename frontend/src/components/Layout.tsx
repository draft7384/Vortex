import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Layout: React.FC = () => {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shrink-0 shadow-sm">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-bold text-vortex-primary">Vortex</span>
            <span className="text-slate-300">/</span>
            <span className="text-slate-500 text-sm font-medium">Sistema de Facturación</span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right mr-2">
              <p className="text-xs text-slate-400 uppercase font-bold">Soporte</p>
              <p className="text-sm font-medium text-slate-600">v1.0.0-stable</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-slate-200 border-2 border-white shadow-sm"></div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
