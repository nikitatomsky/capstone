import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { Assignment } from '../types/models';
import { api } from '../services/api';

export default function AssignmentDetail() {
  const { id } = useParams<{ id: string }>();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      api.getAssignment(id)
        .then(setAssignment)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <main className="main">
        <div className="container">
          <div className="empty-state">
            <div className="empty-state__content">
              <p>Loading assignment details...</p>
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
            <p><strong>Error:</strong> {error}</p>
          </div>
        </div>
      </main>
    );
  }

  if (!assignment) {
    return (
      <main className="main">
        <div className="container">
          <div className="empty-state">
            <div className="empty-state__content">
              <h3 className="empty-state__title">Assignment not found</h3>
              <Link to="/" className="btn btn--primary">Back to Dashboard</Link>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="main">
      <div className="container container--narrow">
        {/* Page Header */}
        <div className="page-header">
          <div className="page-header__content">
            <Link to="/" className="back-link">← Back to Assignments</Link>
            <h2 className="page-header__title">{assignment.title}</h2>
            <div className="assignment-card__meta" style={{ marginTop: 'var(--space-3)' }}>
              <span className={`badge badge--priority badge--${assignment.priority}`}>
                {assignment.priority}
              </span>
              <span className={`badge badge--status badge--${assignment.status.replace('_', '-')}`}>
                {assignment.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Assignment Details Card */}
        <article className="assignment-card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="assignment-card__body">
            <h3 style={{ 
              fontSize: '0.875rem', 
              fontWeight: 600, 
              color: 'var(--color-neutral-900)', 
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: 'var(--space-4)'
            }}>
              Assignment Details
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <dt style={{ 
                  fontSize: '0.75rem', 
                  fontWeight: 600, 
                  color: 'var(--color-neutral-600)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 'var(--space-1)'
                }}>
                  Description
                </dt>
                <dd style={{ 
                  color: 'var(--color-neutral-900)', 
                  lineHeight: 1.6,
                  fontSize: '0.9375rem'
                }}>
                  {assignment.description}
                </dd>
              </div>

              <div>
                <dt style={{ 
                  fontSize: '0.75rem', 
                  fontWeight: 600, 
                  color: 'var(--color-neutral-600)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 'var(--space-1)'
                }}>
                  Assigned To
                </dt>
                <dd style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span className="tech-avatar">
                    {assignment.technician_name.split(' ').map(n => n[0]).join('')}
                  </span>
                  <span className="tech-name">{assignment.technician_name}</span>
                </dd>
              </div>

              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 'var(--space-4)',
                paddingTop: 'var(--space-4)',
                borderTop: '1px solid var(--color-neutral-200)'
              }}>
                <div>
                  <dt style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 600, 
                    color: 'var(--color-neutral-600)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: 'var(--space-1)'
                  }}>
                    Created
                  </dt>
                  <dd style={{ color: 'var(--color-neutral-900)', fontSize: '0.875rem' }}>
                    {new Date(assignment.created_at).toLocaleString()}
                  </dd>
                </div>

                {assignment.assigned_at && (
                  <div>
                    <dt style={{ 
                      fontSize: '0.75rem', 
                      fontWeight: 600, 
                      color: 'var(--color-neutral-600)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      marginBottom: 'var(--space-1)'
                    }}>
                      Assigned
                    </dt>
                    <dd style={{ color: 'var(--color-neutral-900)', fontSize: '0.875rem' }}>
                      {new Date(assignment.assigned_at).toLocaleString()}
                    </dd>
                  </div>
                )}

                {assignment.completed_at && (
                  <div>
                    <dt style={{ 
                      fontSize: '0.75rem', 
                      fontWeight: 600, 
                      color: 'var(--color-neutral-600)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      marginBottom: 'var(--space-1)'
                    }}>
                      Completed
                    </dt>
                    <dd style={{ color: 'var(--color-neutral-900)', fontSize: '0.875rem' }}>
                      {new Date(assignment.completed_at).toLocaleString()}
                    </dd>
                  </div>
                )}
              </div>
            </div>
          </div>
        </article>

        {/* Intake Record Card */}
        {assignment.intake_record_id && (
          <article className="assignment-card">
            <div className="assignment-card__body">
              <h3 style={{ 
                fontSize: '0.875rem', 
                fontWeight: 600, 
                color: 'var(--color-neutral-900)', 
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: 'var(--space-4)'
              }}>
                Intake Record
              </h3>
              <div>
                <dt style={{ 
                  fontSize: '0.75rem', 
                  fontWeight: 600, 
                  color: 'var(--color-neutral-600)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: 'var(--space-1)'
                }}>
                  Record ID
                </dt>
                <dd style={{ 
                  color: 'var(--color-neutral-900)', 
                  fontSize: '0.875rem',
                  fontFamily: 'var(--font-mono)'
                }}>
                  {assignment.intake_record_id}
                </dd>
              </div>
            </div>
          </article>
        )}
      </div>
    </main>
  );
}
