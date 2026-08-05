import type { Assignment, AssignmentCreate, Technician, TechnicianCreate, TelegramInvitationResponse } from '../types/models';

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

  // Technicians (Full CRUD)
  async getTechnicians(): Promise<Technician[]> {
    const response = await fetch(`${API_BASE_URL}/api/technicians`);
    if (!response.ok) throw new Error('Failed to fetch technicians');
    return response.json();
  },

  async getTechnician(id: string): Promise<Technician> {
    const response = await fetch(`${API_BASE_URL}/api/technicians/${id}`);
    if (!response.ok) throw new Error('Failed to fetch technician');
    return response.json();
  },

  async createTechnician(data: TechnicianCreate): Promise<Technician> {
    const response = await fetch(`${API_BASE_URL}/api/technicians`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create technician');
    }
    return response.json();
  },

  async deleteTechnician(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/technicians/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete technician');
    }
  },

  async sendTechnicianInvitation(technicianId: string, deliveryMethod: 'email' | 'sms' = 'email'): Promise<TelegramInvitationResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/technicians/${technicianId}/telegram-invitation?delivery_method=${deliveryMethod}`,
      { method: 'POST' }
    );
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send invitation');
    }
    return response.json();
  },
};
