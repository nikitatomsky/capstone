import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import AssignmentList from './components/AssignmentList';
import AssignmentDetail from './components/AssignmentDetail';
import CreateAssignmentForm from './components/CreateAssignmentForm';
import TechnicianList from './components/TechnicianList';
import CreateTechnicianForm from './components/CreateTechnicianForm';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div>
        <header className="header">
          <div className="container">
            <div className="header__content">
              <h1 className="header__title">Field Intake Service</h1>
              <nav className="header__nav" aria-label="Main navigation">
                <ul role="list">
                  <li><Link to="/">Assignments</Link></li>
                  <li><Link to="/create">Create Assignment</Link></li>
                  <li><Link to="/technicians">Technicians</Link></li>
                  <li><Link to="/technicians/create">Add Technician</Link></li>
                </ul>
              </nav>
            </div>
          </div>
        </header>

        <Routes>
          <Route path="/" element={<AssignmentList />} />
          <Route path="/assignments/:id" element={<AssignmentDetail />} />
          <Route path="/create" element={<CreateAssignmentForm />} />
          <Route path="/technicians" element={<TechnicianList />} />
          <Route path="/technicians/create" element={<CreateTechnicianForm />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
