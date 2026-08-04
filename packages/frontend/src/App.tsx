import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import AssignmentList from './components/AssignmentList';
import AssignmentDetail from './components/AssignmentDetail';
import CreateAssignmentForm from './components/CreateAssignmentForm';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh' }}>
        <nav style={{ 
          padding: '20px', 
          backgroundColor: '#f5f5f5', 
          borderBottom: '1px solid #ddd',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <h2 style={{ margin: 0 }}>Assignment Dashboard</h2>
            <Link to="/" style={{ textDecoration: 'none', color: '#007bff' }}>Assignments</Link>
            <Link to="/create" style={{ textDecoration: 'none', color: '#007bff' }}>Create Assignment</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<AssignmentList />} />
          <Route path="/assignments/:id" element={<AssignmentDetail />} />
          <Route path="/create" element={<CreateAssignmentForm />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
