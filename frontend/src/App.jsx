import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

const PaginaHome = () => <h1 style={{color: 'blue'}}>VOCÊ ESTÁ NA HOME</h1>;
const PaginaScrapme = () => <h1 style={{color: 'green'}}>VOCÊ ESTÁ NA SCRAPME</h1>;

function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: '20px', borderBottom: '1px solid #ccc' }}>
        <Link to="/">Ir para Home</Link> | 
        <Link to="/scrapme" style={{ marginLeft: '10px' }}>Ir para Scrapme</Link>
      </nav>

      <div style={{ padding: '20px' }}>
        <Routes>
          <Route path="/" element={<PaginaHome />} />
          <Route path="/scrapme" element={<PaginaScrapme />} />
          {/* Rota de segurança para qualquer erro de digitação na URL */}
          <Route path="*" element={<h1>Ops! Caminho não encontrado.</h1>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;