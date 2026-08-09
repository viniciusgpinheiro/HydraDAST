import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NovoScan from './pages/NovoScan';
import Relatorios from './pages/Relatorios';
import Relatorio from './pages/Relatorio';
import Configuracoes from './pages/Configuracoes';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/novo-scan" element={<NovoScan />} />
          <Route path="/relatorios" element={<Relatorios />} />
          <Route path="/relatorios/:id" element={<Relatorio />} />
          <Route path="/relatorio" element={<Relatorio />} />
          <Route path="/configuracoes" element={<Configuracoes />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
