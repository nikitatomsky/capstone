import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Technician } from '../types/models';
import { api } from '../services/api';

export default function TechnicianList() {
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadTechnicians = () => {
    api.getTechnicians()
      .then(setTechnicians)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTechnicians();
  }, []);

  const handleDelete = async (technicianId: string, technicianName: string) => {
    if (!confirm(`Delete technician "${technicianName}"? This cannot be undone.`)) {
      return;
    }

    setDeleteError(null);
    try {
      await api.deleteTechnician(technicianId);
      // Reload list after successful deletion
      loadTechnicians();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete technician');
    }
  };

  if (loading) return <div style={{ padding: '20px' }}>Loading...</div>;
  if (error) return <div style={{ padding: '20px', color: 'red' }}>Error: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Technicians</h1>
        <Link to="/technicians/create" style={{ 
          padding: '10px 20px', 
          backgroundColor: '#007bff', 
          color: 'white', 
          textDecoration: 'none',
          borderRadius: '4px'
        }}>
          + Add Technician
        </Link>
      </div>

      {deleteError && (
        <div style={{ 
          padding: '10px', 
          marginBottom: '15px', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c00'
        }}>
          {deleteError}
        </div>
      )}

      {technicians.length === 0 ? (
        <p>No technicians found. <Link to="/technicians/create">Create one</Link></p>
      ) : (
        <div style={{ display: 'grid', gap: '15px' }}>
          {technicians.map(technician => (
            <div 
              key={technician.technician_id} 
              style={{ 
                padding: '15px', 
                border: '1px solid #ddd',
                borderRadius: '4px',
                backgroundColor: '#f9f9f9'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: '0 0 10px 0' }}>{technician.name}</h3>
                  <div style={{ fontSize: '0.9em', color: '#666' }}>
                    <div>📞 Phone: {technician.phone_number}</div>
                    <div>💬 Telegram: {technician.chat_id ? `ID ${technician.chat_id}` : 'Not connected'}</div>
                    <div>📅 Registered: {new Date(technician.registered_at).toLocaleDateString()}</div>
                    <div style={{ fontSize: '0.85em', marginTop: '5px', color: '#999' }}>
                      ID: {technician.technician_id}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(technician.technician_id, technician.name)}
                  style={{ 
                    padding: '6px 12px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#c82333'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#dc3545'}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
