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
  email?: string; // Optional email for invitations
  chat_id: number | null; // Optional Telegram integration
  registered_at: string;
  invitation_status?: 'pending' | 'sent' | 'connected'; // Invitation state
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
  email?: string; // Optional email for invitations
  chat_id?: number | null; // Optional Telegram chat_id
}

export interface TelegramInvitationResponse {
  success: boolean;
  delivery_method: string;
  destination: string;
  invitation_link: string;
  expires_at: string | null;
  delivery_attempted: boolean;
  delivery_succeeded: boolean;
}
