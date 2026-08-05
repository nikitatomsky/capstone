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
  const [errors, setErrors] = useState<Record<string, string>>({});
  
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
    
    // Validate
    const newErrors: Record<string, string> = {};
    if (!formData.title.trim()) newErrors.title = 'Title is required';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    if (!formData.technician_id) newErrors.technician_id = 'Please select a technician';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setError(null);
    setErrors({});

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
    <main className="main">
      <div className="container">
        <div className="page-header">
          <div className="page-header__content">
            <h2 className="page-header__title">Create Assignment</h2>
            <p className="page-header__subtitle">
              Assign a new task to a field technician
            </p>
          </div>
        </div>

        {error && (
          <div className="info-box" style={{
            borderColor: 'var(--color-danger)',
            backgroundColor: 'var(--color-danger-light)',
            marginBottom: 'var(--space-6)'
          }}>
            <p style={{ margin: 0 }}>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="form" style={{ maxWidth: '600px' }}>
          <div className="form-group">
            <label htmlFor="technician_id" className="form-label">
              Technician <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <select
              id="technician_id"
              value={formData.technician_id}
              onChange={(e) => setFormData({ ...formData, technician_id: e.target.value })}
              required
              className="form-input"
            >
              <option value="">Select a technician</option>
              {technicians.map(tech => (
                <option key={tech.technician_id} value={tech.technician_id}>
                  {tech.name} - {tech.phone_number}
                </option>
              ))}
            </select>
            {errors.technician_id && (
              <span className="form-hint" style={{ color: 'var(--color-danger)' }}>
                {errors.technician_id}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="title" className="form-label">
              Title <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              placeholder="e.g., HVAC Repair at 123 Main St"
              className="form-input"
            />
            {errors.title && (
              <span className="form-hint" style={{ color: 'var(--color-danger)' }}>
                {errors.title}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="description" className="form-label">
              Description <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              rows={4}
              placeholder="Provide details about the service call..."
              className="form-input"
            />
            {errors.description && (
              <span className="form-hint" style={{ color: 'var(--color-danger)' }}>
                {errors.description}
              </span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="priority" className="form-label">
              Priority
            </label>
            <select
              id="priority"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              className="form-input"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            <span className="form-hint">
              Urgent assignments are highlighted for immediate attention
            </span>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button 
              type="submit" 
              disabled={loading} 
              className="btn btn--primary"
            >
              {loading ? 'Creating...' : 'Create Assignment'}
            </button>
            <button 
              type="button" 
              onClick={() => navigate('/')} 
              className="btn btn--secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
