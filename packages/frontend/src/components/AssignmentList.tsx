import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Assignment } from '../types/models';
import { api } from '../services/api';
import { AssignmentSSEClient } from '../services/sse';

export default function AssignmentList() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Initial load
    api.getAssignments()
      .then(setAssignments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));

    // Real-time updates
    const sseClient = new AssignmentSSEClient();
    sseClient.connect((updatedAssignment) => {
      setAssignments(prev =>
        prev.map(a => a.assignment_id === updatedAssignment.assignment_id
          ? updatedAssignment
          : a
        )
      );
    });

    return () => sseClient.disconnect();
  }, []);

  if (loading) {
    return (
      <main className="main">
        <div className="container">
          <div className="empty-state">
            <div className="empty-state__content">
              <p>Loading assignments...</p>
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
            <h2 className="page-header__title">Active Assignments</h2>
            <p className="page-header__subtitle">
              Manage and track field service assignments
            </p>
          </div>
          <div className="page-header__actions">
            <Link to="/create" className="btn btn--primary">
              + New Assignment
            </Link>
          </div>
        </div>

        {/* Assignment Cards */}
        {assignments.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state__content">
              <h3 className="empty-state__title">No assignments yet</h3>
              <p className="empty-state__description">
                Create your first assignment to get started
              </p>
              <Link to="/create" className="btn btn--primary">
                Create Assignment
              </Link>
            </div>
          </div>
        ) : (
          <div className="assignment-grid">
            {assignments.map(assignment => (
              <article key={assignment.assignment_id} className="assignment-card">
                <div className="assignment-card__header">
                  <div className="assignment-card__meta">
                    <span className={`badge badge--priority badge--${assignment.priority}`}>
                      {assignment.priority}
                    </span>
                    <span className={`badge badge--status badge--${assignment.status.replace('_', '-')}`}>
                      {assignment.status.replace('_', ' ')}
                    </span>
                  </div>
                  <time className="assignment-card__time">
                    {new Date(assignment.created_at).toLocaleString()}
                  </time>
                </div>
                
                <div className="assignment-card__body">
                  <h3 className="assignment-card__title">{assignment.title}</h3>
                  <p className="assignment-card__description">
                    {assignment.description}
                  </p>
                  <div className="assignment-card__tech">
                    <span className="tech-avatar">
                      {assignment.technician_name.split(' ').map(n => n[0]).join('')}
                    </span>
                    <span className="tech-name">{assignment.technician_name}</span>
                  </div>
                </div>
                
                <footer className="assignment-card__footer">
                  <Link
                    to={`/assignments/${assignment.assignment_id}`}
                    className="link"
                  >
                    View Details →
                  </Link>
                </footer>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
