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

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!assignment) return <div>Assignment not found</div>;

  return (
    <div style={{ padding: '20px' }}>
      <Link to="/">← Back to Assignments</Link>
      <h1>{assignment.title}</h1>
      <div style={{ marginTop: '20px' }}>
        <p><strong>Status:</strong> {assignment.status}</p>
        <p><strong>Priority:</strong> {assignment.priority}</p>
        <p><strong>Technician:</strong> {assignment.technician_name}</p>
        <p><strong>Description:</strong> {assignment.description}</p>
        <p><strong>Created:</strong> {new Date(assignment.created_at).toLocaleString()}</p>
        {assignment.assigned_at && (
          <p><strong>Assigned:</strong> {new Date(assignment.assigned_at).toLocaleString()}</p>
        )}
        {assignment.completed_at && (
          <p><strong>Completed:</strong> {new Date(assignment.completed_at).toLocaleString()}</p>
        )}
        {assignment.intake_record_id && (
          <p><strong>Intake Record ID:</strong> {assignment.intake_record_id}</p>
        )}
      </div>
    </div>
  );
}
