import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function CreateTechnicianForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const [formData, setFormData] = useState({
    name: '',
    phone_number: '',
    email: '',
    chat_id: '',
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setErrors({});

    // Validate
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setLoading(false);
      return;
    }

    try {
      const payload = {
        name: formData.name,
        phone_number: formData.phone_number,
        // Only include email if provided
        ...(formData.email && { email: formData.email }),
        // Only include chat_id if provided
        ...(formData.chat_id && { chat_id: parseInt(formData.chat_id) }),
      };

      await api.createTechnician(payload);
      navigate('/technicians');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create technician');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="main">
      <div className="container">
        <div className="page-header">
          <div className="page-header__content">
            <h2 className="page-header__title">Add Technician</h2>
            <p className="page-header__subtitle">
              Register a new field service technician
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
            <label htmlFor="name" className="form-label">
              Name <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="John Doe"
              className="form-input"
            />
            {errors.name && <span className="form-hint" style={{ color: 'var(--color-danger)' }}>{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email <span style={{ color: 'var(--color-danger)' }}>*</span>
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              required
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="john@example.com"
              className="form-input"
            />
            <span className="form-hint">
              Required for completing onboarding. 
            </span>
            {errors.email && <span className="form-hint" style={{ color: 'var(--color-danger)' }}>{errors.email}</span>}

          </div>

          <div className="form-group">
            <label htmlFor="phone_number" className="form-label">
              Phone Number 
            </label>
            <input
              id="phone_number"
              type="tel"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              placeholder="+1-555-123-4567"
              className="form-input"
            />
            <span className="form-hint">
              Used for SMS notifications if no email provided
            </span>
            {errors.phone_number && <span className="form-hint" style={{ color: 'var(--color-danger)' }}>{errors.phone_number}</span>}
          </div>



          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button 
              type="submit" 
              disabled={loading} 
              className="btn btn--primary"
            >
              {loading ? 'Creating...' : 'Create Technician'}
            </button>
            <button 
              type="button" 
              onClick={() => navigate('/technicians')} 
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
