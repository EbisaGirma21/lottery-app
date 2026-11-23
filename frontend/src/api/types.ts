/**
 * TypeScript interfaces matching the Django backend data contracts.
 */

export type UserRole =
  | 'super_admin'
  | 'lottery_manager'
  | 'payment_officer'
  | 'draw_officer'
  | 'viewer';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  phone_number?: string;
  last_login?: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export type LotteryStatus =
  | 'draft'
  | 'open'
  | 'paused'
  | 'closed'
  | 'drawn'
  | 'completed'
  | 'cancelled';

export interface PaymentInstruction {
  id?: string;
  payment_method: string;
  account_name: string;
  account_number: string;
  additional_info?: string;
  is_active: boolean;
}

export interface Lottery {
  id: string;
  name: string;
  slug: string;
  description: string;
  ticket_price: string;
  total_numbers: number;
  start_date: string;
  closing_date: string;
  draw_date: string;
  first_prize_name: string;
  first_prize_description?: string;
  first_prize_value: string;
  second_prize_name: string;
  second_prize_description?: string;
  second_prize_value: string;
  third_prize_name: string;
  third_prize_description?: string;
  third_prize_value: string;
  reservation_hours: number;
  max_tickets_per_customer?: number;
  status: LotteryStatus;
  sold_tickets_count?: number;
  reserved_tickets_count?: number;
  available_tickets_count?: number;
  payment_instructions?: PaymentInstruction[];
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  lottery: string;
  ticket_number: string;
  status: 'available' | 'reserved' | 'sold' | 'winner';
  customer?: {
    id: string;
    full_name: string;
    phone_number: string;
    telegram_user_id: number;
  };
  updated_at: string;
}

export type PaymentMethod =
  | 'telebirr'
  | 'cbe'
  | 'cbe_birr'
  | 'awash'
  | 'boa'
  | 'other';

export type PaymentStatus = 'pending' | 'approved' | 'rejected';

export interface Payment {
  id: string;
  customer: {
    id: string;
    full_name: string;
    phone_number: string;
    telegram_user_id: number;
    telegram_username?: string;
  };
  lottery: {
    id: string;
    name: string;
    ticket_price: string;
  };
  reservations: {
    id: string;
    ticket: {
      id: string;
      ticket_number: string;
    };
    expires_at: string;
  }[];
  payment_method: PaymentMethod;
  transaction_reference: string;
  amount: string;
  payment_proof?: string;
  status: PaymentStatus;
  is_auto_verified?: boolean;
  auto_verification_status?: string;
  verification_data?: Record<string, any>;
  verification_error?: string;
  rejection_reason?: string;
  admin_notes?: string;
  reviewed_by?: {
    id: string;
    full_name: string;
    email: string;
  };
  reviewed_at?: string;
  submitted_at: string;
}

export interface Winner {
  id: string;
  position: 1 | 2 | 3;
  position_display: string;
  prize_name: string;
  prize_description?: string;
  prize_value: string;
  customer: {
    id: string;
    full_name: string;
    phone_number: string;
  };
  ticket: {
    id: string;
    ticket_number: string;
  };
  claim_status: 'unclaimed' | 'claimed' | 'expired';
  payout_reference?: string;
  claimed_at?: string;
}

export interface Draw {
  id: string;
  lottery: {
    id: string;
    name: string;
  };
  executed_by: {
    id: string;
    full_name: string;
  };
  executed_at: string;
  randomness_hash: string;
  sold_tickets_pool_count: number;
  winners: Winner[];
}

export interface DashboardAnalytics {
  active_lotteries_count: number;
  total_revenue: string;
  monthly_revenue: string;
  pending_payments_count: number;
  pending_payments_value: string;
  total_tickets_sold: number;
  overall_conversion_rate: number;
  revenue_by_method: {
    method: string;
    display_name: string;
    total: string;
    count: number;
  }[];
  recent_payments: Payment[];
  recent_winners: Winner[];
}

export interface AuditLog {
  id: string;
  actor_email?: string;
  actor_name?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  ip_address?: string;
  old_value?: any;
  new_value?: any;
  timestamp: string;
}

export interface LotteryParticipantPayment {
  id: string;
  payment_method: string;
  payment_method_display: string;
  transaction_reference: string;
  amount: string;
  status: PaymentStatus;
  status_display: string;
  payment_proof?: string | null;
  submitted_at?: string | null;
  tickets: string[];
}

export type ApplicationStatus =
  | 'pending_verification'
  | 'approved_paid'
  | 'reserved_unpaid'
  | 'rejected'
  | 'in_progress';

export interface LotteryParticipant {
  customer_id: string;
  full_name: string;
  phone_number: string;
  telegram_username?: string;
  telegram_user_id: number;
  tickets_sold: string[];
  tickets_reserved: string[];
  payments: LotteryParticipantPayment[];
  application_status: ApplicationStatus;
  total_tickets_count: number;
}

export interface LotteryParticipantsResponse {
  lottery_id: string;
  lottery_name: string;
  total_participants: number;
  participants: LotteryParticipant[];
}

