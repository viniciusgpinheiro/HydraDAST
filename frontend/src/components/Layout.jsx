import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="hd-app">
      <Sidebar />
      <main className="hd-main">
        <div className="hd-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
