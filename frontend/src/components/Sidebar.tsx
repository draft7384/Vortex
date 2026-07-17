import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Users,
  Package,
  Settings,
  LogOut,
  ChevronDown,
  UserCircle
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface MenuItem {
  title: string;
  icon: React.ElementType;
  path?: string;
  children?: { title: string; path: string }[];
}

const MENU_STRUCTURE: MenuItem[] = [
  {
    title: 'Dashboard',
    icon: LayoutDashboard,
    path: '/',
  },
  {
    title: 'Ventas',
    icon: FileText,
    children: [
      { title: 'Facturas', path: '/documentos' },
      { title: 'Notas de Entrega', path: '/documentos/ne' },
      { title: 'NC / ND', path: '/documentos/nc-nd' },
    ],
  },
  {
    title: 'Maestros',
    icon: Users,
    children: [
      { title: 'Clientes', path: '/clientes' },
      { title: 'Productos', path: '/productos' },
      { title: 'Vendedores', path: '/vendedores' },
    ],
  },
  {
    title: 'Configuración',
    icon: Settings,
    children: [
      { title: 'Empresa', path: '/config/empresa' },
      { title: 'Tasas Cambio', path: '/config/tasas' },
      { title: 'Puntos Emisión', path: '/config/puntos' },
    ],
  },
];

const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [expandedMenus, setExpandedMenus] = useState<Record<string, boolean>>({});

  const toggleMenu = (title: string) => {
    setExpandedMenus(prev => ({ ...prev, [title]: !prev[title] }));
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
  };

  return (
    <aside className="h-screen w-64 bg-vortex-dark text-slate-300 flex flex-col border-r border-slate-800 shadow-xl">
      <div className="p-6 flex flex-col items-center border-b border-slate-800">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-vortex-primary flex items-center justify-center text-white text-2xl font-bold shadow-inner border-4 border-slate-700 overflow-hidden">
            {user?.nombre_completo ? (
              <span>{getInitials(user.nombre_completo)}</span>
            ) : (
              <UserCircle size={40} />
            )}
          </div>
          <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-vortex-dark rounded-full"></div>
        </div>
        <div className="mt-3 text-center">
          <p className="text-white font-semibold truncate w-40">{user?.nombre_completo || 'Usuario Vortex'}</p>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">{user?.rol || 'ADMIN'}</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {MENU_STRUCTURE.map((item) => (
          <div key={item.title} className="mb-1">
            {item.children ? (
              <div>
                <button
                  onClick={() => toggleMenu(item.title)}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-800 transition-all group"
                >
                  <div className="flex items-center space-x-3">
                    <item.icon size={20} className="text-slate-400 group-hover:text-white transition-colors" />
                    <span className="font-medium text-sm">{item.title}</span>
                  </div>
                  <span className={`transition-transform duration-200 ${expandedMenus[item.title] ? 'rotate-180' : ''}`}>
                    <ChevronDown size={16} />
                  </span>
                </button>

                <div className={`overflow-hidden transition-all duration-300 ${expandedMenus[item.title] ? 'max-h-60 opacity-100' : 'max-h-0 opacity-0'}`}>
                  <div className="pl-9 pr-3 py-1 space-y-1">
                    {item.children.map(child => (
                      <Link
                        key={child.path}
                        to={child.path}
                        className="block px-3 py-2 text-sm rounded-md hover:bg-slate-800 hover:text-white transition-all text-slate-400"
                      >
                        {child.title}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <Link
                to={item.path || '/'}
                className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-slate-800 transition-all group"
              >
                <item.icon size={20} className="text-slate-400 group-hover:text-white transition-colors" />
                <span className="font-medium text-sm">{item.title}</span>
              </Link>
            )}
          </div>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={() => {
            logout();
            navigate('/login');
          }}
          className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-all group"
        >
          <LogOut size={20} className="group-hover:text-red-400 transition-colors" />
          <span className="font-medium text-sm">Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
