/**
 * TypeScript interfaces matching backend API models
 */

export interface Assignment {
  assignment_id: string;
  technician_chat_id: number;
  technician_name: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  created_at: string;
  assigned_at: string | null;
  completed_at: string | null;
  intake_record_id: string | null;
}

export interface Technician {
  chat_id: number;
  name: string;
  registered_at: string;
}

export interface AssignmentCreate {
  technician_chat_id: number;
  technician_name: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
}
