import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { toast, Toaster } from 'react-hot-toast';
import { Lock, User, Eye, EyeOff, LogIn, ShieldCheck } from 'lucide-react';

const Login = () => {
  const { login, isLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem('remember_username');
    const savedPass = localStorage.getItem('remember_password');
    if (savedUser) setUsername(savedUser);
    if (savedPass) setPassword(savedPass);
    if (savedUser && savedPass) setRememberMe(true);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      toast.error('Por favor, complete todos los campos');
      return;
    }

    const result = await login(username, password);

    if (result.success) {
      toast.success(result.message);
    } else {
      toast.error(result.message);
    }

    if (rememberMe) {
      localStorage.setItem('remember_username', username);
      localStorage.setItem('remember_password', password);
    } else {
      localStorage.removeItem('remember_username');
      localStorage.removeItem('remember_password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <Toaster position="top-right" />

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-vortex-primary text-white mb-4 shadow-lg shadow-vortex-primary/30">
            <ShieldCheck size={40} />
          </div>
          <h1 className="text-3xl font-bold text-slate-800">Vortex System</h1>
          <p className="text-slate-500 mt-2">Gestión de Facturación y CxC</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 transition-all">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 ml-1">Usuario</label>
              <div className="relative group">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-vortex-primary transition-colors">
                  <User size={18} />
                </span>
                <input
                  type="text"
                  className="input-field pl-10"
                  placeholder="Ingrese su usuario"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-sm font-medium text-slate-700">Contraseña</label>
                <a href="#" className="text-xs text-vortex-primary hover:underline font-medium transition-colors">
                  ¿Olvidó su contraseña?
                </a>
              </div>
              <div className="relative group">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-vortex-primary transition-colors">
                  <Lock size={18} />
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-field pl-10"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2 ml-1">
              <input
                id="remember"
                type="checkbox"
                className="w-4 h-4 rounded border-slate-300 text-vortex-primary focus:ring-vortex-primary"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <label htmlFor="remember" className="text-sm text-slate-600 cursor-pointer select-none">
                Recordarme en este equipo
              </label>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center space-x-2 py-3"
            >
              {isLoading ? (
                <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
              ) : (
                <LogIn size={20} />
              )}
              <span className="font-medium">Ingresar al Sistema</span>
            </button>
          </form>
        </div>

        <p className="text-center text-slate-400 text-sm mt-8">
          &copy; {new Date().getFullYear()} Vortex ERP - Todos los derechos reservados.
        </p>
      </div>
    </div>
  );
};

export default Login;
