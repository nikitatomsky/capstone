import type { Assignment, AssignmentCreate, Technician } from '../types/models';

const API_BASE_URL = 'http://localhost:4000';

export const api = {
  // Assignments
  async getAssignments(): Promise<Assignment[]> {
    const response = await fetch(`${API_BASE_URL}/api/assignments`);
    if (!response.ok) throw new Error('Failed to fetch assignments');
    return response.json();
  },

  async getAssignment(id: string): Promise<Assignment> {
    const response = await fetch(`${API_BASE_URL}/api/assignments/${id}`);
    if (!response.ok) throw new Error('Failed to fetch assignment');
    return response.json();
  },

  async createAssignment(data: AssignmentCreate): Promise<Assignment> {
    const response = await fetch(`${API_BASE_URL}/api/assignments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create assignment');
    return response.json();
  },

  // Technicians
  async getTechnicians(): Promise<Technician[]> {
    const response = await fetch(`${API_BASE_URL}/api/technicians`);
    if (!response.ok) throw new Error('Failed to fetch technicians');
    return response.json();
  },
};
