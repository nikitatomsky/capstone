/**
 * TypeScript interfaces matching backend API models
 * Updated for Issue #30: UUID-based technician references
 */

export interface Assignment {
  assignment_id: string;
  technician_id: string; // UUID reference
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
  technician_id: string; // UUID primary key
  name: string;
  phone_number: string;
  chat_id: number | null; // Optional Telegram integration
  registered_at: string;
}

export interface AssignmentCreate {
  technician_id: string; // UUID reference
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
}

export interface TechnicianCreate {
  name: string;
  phone_number: string;
  chat_id?: number | null; // Optional Telegram chat_id
}
