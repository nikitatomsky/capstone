import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { Technician } from '../types/models';

export default function CreateAssignmentForm() {
  const navigate = useNavigate();
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    technician_id: '',
    title: '',
    description: '',
    priority: 'medium' as const,
  });

  useEffect(() => {
    api.getTechnicians().then(setTechnicians).catch(console.error);
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.createAssignment(formData);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create assignment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h1>Create Assignment</h1>
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Technician:
            <select
              value={formData.technician_id}
              onChange={(e) => setFormData({ ...formData, technician_id: e.target.value })}
              required
              style={{ display: 'block', width: '100%', padding: '5px', marginTop: '5px' }}
            >
              <option value="">Select a technician</option>
              {technicians.map(tech => (
                <option key={tech.technician_id} value={tech.technician_id}>
                  {tech.name} - {tech.phone_number}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            Title:
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              style={{ display: 'block', width: '100%', padding: '5px', marginTop: '5px' }}
            />
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            Description:
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              rows={4}
              style={{ display: 'block', width: '100%', padding: '5px', marginTop: '5px' }}
            />
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            Priority:
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              style={{ display: 'block', width: '100%', padding: '5px', marginTop: '5px' }}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button type="submit" disabled={loading} style={{ padding: '10px 20px' }}>
            {loading ? 'Creating...' : 'Create Assignment'}
          </button>
          <button type="button" onClick={() => navigate('/')} style={{ padding: '10px 20px' }}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
