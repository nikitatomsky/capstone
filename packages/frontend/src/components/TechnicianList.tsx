import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Technician } from '../types/models';
import { api } from '../services/api';

export default function TechnicianList() {
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [loadingTechId, setLoadingTechId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  const loadTechnicians = () => {
    api.getTechnicians()
      .then((techs) => {
        // Derive invitation status from chat_id
        const techsWithStatus = techs.map(tech => ({
          ...tech,
          invitation_status: tech.chat_id ? 'connected' as const : 'pending' as const
        }));
        setTechnicians(techsWithStatus);
      })
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

  const handleSendInvitation = async (technicianId: string) => {
    setLoadingTechId(technicianId);
    setNotification(null);
    try {
      const technician = technicians.find(t => t.technician_id === technicianId);
      const deliveryMethod = technician?.email ? 'email' : 'sms';
      
      const result = await api.sendTechnicianInvitation(technicianId, deliveryMethod);
      
      setNotification({
        type: 'success',
        message: `Invitation sent via ${result.delivery_method} to ${result.destination}!`
      });
      
      // Update technician status
      setTechnicians(prev => prev.map(tech => 
        tech.technician_id === technicianId 
          ? { ...tech, invitation_status: 'sent' as const }
          : tech
      ));
    } catch (err) {
      setNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to send invitation. Please try again.'
      });
    } finally {
      setLoadingTechId(null);
      setTimeout(() => setNotification(null), 5000);
    }
  };

  const handleResendInvitation = async (technicianId: string) => {
    await handleSendInvitation(technicianId);
  };

  if (loading) {
    return (
      <main className="main">
        <div className="container">
          <div className="empty-state">
            <div className="empty-state__content">
              <p>Loading technicians...</p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="main">
        <div className="container">
          <div className="info-box" style={{
            borderColor: 'var(--color-danger)',
            backgroundColor: 'var(--color-danger-light)'
          }}>
            <p>Error: {error}</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="main">
      <div className="container">
        {/* Page Header */}
        <div className="page-header">
          <div className="page-header__content">
            <h2 className="page-header__title">Technicians</h2>
            <p className="page-header__subtitle">
              Manage field service technicians and send chat invitations
            </p>
          </div>
          <div className="page-header__actions">
            <Link to="/technicians/create" className="btn btn--primary">
              + Add Technician
            </Link>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div 
            className="info-box" 
            style={{
              borderColor: notification.type === 'success' ? 'var(--color-success)' : 'var(--color-danger)',
              backgroundColor: notification.type === 'success' ? 'var(--color-success-light)' : 'var(--color-danger-light)',
              marginBottom: 'var(--space-6)',
              position: 'relative'
            }}
          >
            <p style={{ margin: 0 }}>{notification.message}</p>
            <button
              onClick={() => setNotification(null)}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.5rem',
                lineHeight: 1
              }}
            >
              ×
            </button>
          </div>
        )}

        {/* Delete Error */}
        {deleteError && (
          <div className="info-box" style={{
            borderColor: 'var(--color-danger)',
            backgroundColor: 'var(--color-danger-light)',
            marginBottom: 'var(--space-6)'
          }}>
            <p style={{ margin: 0 }}>{deleteError}</p>
          </div>
        )}

        {/* Technician List */}
        {technicians.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__content">
              <h3 className="empty-state__title">No technicians yet</h3>
              <p className="empty-state__description">
                Add your first technician to start managing field service assignments
              </p>
              <Link to="/technicians/create" className="btn btn--primary">
                Add Technician
              </Link>
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
            {technicians.map(technician => (
              <article 
                key={technician.technician_id}
                className="assignment-card"
              >
                <div className="assignment-card__header">
                  <h3 className="assignment-card__title">{technician.name}</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                    {/* Status Badge */}
                    {technician.chat_id ? (
                      <span className="badge badge--status badge--completed">Connected</span>
                    ) : technician.invitation_status === 'sent' ? (
                      <span className="badge badge--status badge--pending">Invitation Sent</span>
                    ) : (
                      <span className="badge badge--status badge--pending">Pending</span>
                    )}
                  </div>
                </div>

                <div className="assignment-card__body">
                  <div style={{ display: 'grid', gap: 'var(--space-2)', fontSize: '0.9em', color: 'var(--color-text-secondary)' }}>
                    <div>📞 Phone: {technician.phone_number}</div>
                    {technician.email && <div>📧 Email: {technician.email}</div>}
                    <div>💬 Telegram: {technician.chat_id ? `ID ${technician.chat_id}` : 'Not connected'}</div>
                    <div>📅 Registered: {new Date(technician.registered_at).toLocaleDateString()}</div>
                    <div style={{ fontSize: '0.85em', color: 'var(--color-text-tertiary)' }}>
                      ID: {technician.technician_id}
                    </div>
                  </div>
                </div>

                <footer className="assignment-card__footer" style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
                  {/* Invitation Action */}
                  {!technician.chat_id && (
                    <>
                      {technician.invitation_status === 'sent' ? (
                        <button
                          className="btn btn--secondary btn--small"
                          onClick={() => handleResendInvitation(technician.technician_id)}
                          disabled={loadingTechId === technician.technician_id}
                        >
                          {loadingTechId === technician.technician_id ? 'Sending...' : 'Resend Invitation'}
                        </button>
                      ) : (
                        <button
                          className="btn btn--primary btn--small"
                          onClick={() => handleSendInvitation(technician.technician_id)}
                          disabled={loadingTechId === technician.technician_id}
                        >
                          {loadingTechId === technician.technician_id ? 'Sending...' : 'Invite to Chat'}
                        </button>
                      )}
                    </>
                  )}

                  {/* Delete Button */}
                  <button
                    onClick={() => handleDelete(technician.technician_id, technician.name)}
                    className="btn btn--danger btn--small"
                  >
                    Delete
                  </button>
                </footer>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
