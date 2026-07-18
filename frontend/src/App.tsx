import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ClientesPage from './pages/Clientes';
import ProductosPage from './pages/Productos';

function App() {
  const { token } = useAuth();

  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas Públicas */}
        <Route path="/login" element={!token ? <Login /> : <Navigate to="/" />} />

        {/* Rutas Protegidas */}
        <Route
          element={
            token ? (
              <Layout />
            ) : (
              <Navigate to="/login" />
            )
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/clientes" element={<ClientesPage />} />
          <Route path="/productos" element={<ProductosPage />} />
          <Route path="*" element={<div className="p-8 text-center font-medium text-slate-500">Página en Construcción 🚧</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
