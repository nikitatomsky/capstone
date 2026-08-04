import type { Assignment } from '../types/models';

export type AssignmentUpdateHandler = (assignment: Assignment) => void;

export class AssignmentSSEClient {
  private eventSource: EventSource | null = null;

  connect(onUpdate: AssignmentUpdateHandler) {
    this.eventSource = new EventSource('http://localhost:4000/api/assignments/stream');

    this.eventSource.addEventListener('assignment_update', (event) => {
      const assignment: Assignment = JSON.parse(event.data);
      onUpdate(assignment);
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      // Implement reconnection logic if needed
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
