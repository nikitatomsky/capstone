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

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Assignments</h1>
      {assignments.length === 0 ? (
        <p>No assignments found.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {assignments.map(assignment => (
            <li key={assignment.assignment_id} style={{ marginBottom: '10px', padding: '10px', border: '1px solid #ddd' }}>
              <Link to={`/assignments/${assignment.assignment_id}`}>
                <strong>{assignment.title}</strong> - {assignment.status}
              </Link>
              <div style={{ fontSize: '0.9em', color: '#666' }}>
                Technician: {assignment.technician_name} | Priority: {assignment.priority}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
