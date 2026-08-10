import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ScanLine, FileBarChart2, Settings } from 'lucide-react';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/novo-scan', label: 'Novo scan', icon: ScanLine },
  { to: '/relatorios', label: 'Relatórios', icon: FileBarChart2 },
  { to: '/configuracoes', label: 'Configurações', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="hd-sidebar">
      <div className="hd-logo">Hydra<span>DAST</span></div>

      <nav className="hd-nav">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => `hd-nav-link${isActive ? ' active' : ''}`}
            >
              <Icon size={22} className="hd-nav-icon" />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
