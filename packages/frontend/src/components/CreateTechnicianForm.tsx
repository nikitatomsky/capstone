import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

export default function CreateTechnicianForm() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    name: '',
    phone_number: '',
    chat_id: '',
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        name: formData.name,
        phone_number: formData.phone_number,
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
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h1>Create Technician</h1>
      
      {error && (
        <div style={{ 
          padding: '10px', 
          marginBottom: '15px', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c00'
        }}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>
            Name: <span style={{ color: 'red' }}>*</span>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="John Doe"
              style={{ 
                display: 'block', 
                width: '100%', 
                padding: '8px', 
                marginTop: '5px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            Phone Number: <span style={{ color: 'red' }}>*</span>
            <input
              type="tel"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              required
              placeholder="+1-555-123-4567"
              style={{ 
                display: 'block', 
                width: '100%', 
                padding: '8px', 
                marginTop: '5px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
            <small style={{ color: '#666', fontSize: '0.85em' }}>
              Used for SMS notifications and contact
            </small>
          </label>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            Telegram Chat ID (optional):
            <input
              type="number"
              value={formData.chat_id}
              onChange={(e) => setFormData({ ...formData, chat_id: e.target.value })}
              placeholder="123456789"
              style={{ 
                display: 'block', 
                width: '100%', 
                padding: '8px', 
                marginTop: '5px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
            <small style={{ color: '#666', fontSize: '0.85em' }}>
              Leave empty if technician hasn't connected via Telegram yet
            </small>
          </label>
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button 
            type="submit" 
            disabled={loading} 
            style={{ 
              padding: '10px 20px',
              backgroundColor: loading ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Creating...' : 'Create Technician'}
          </button>
          <button 
            type="button" 
            onClick={() => navigate('/technicians')} 
            style={{ 
              padding: '10px 20px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
