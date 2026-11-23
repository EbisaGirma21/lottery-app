/**
 * API Type Definitions for Lottery Staff Mobile Application
 */

export interface User {
  id: string;
  email: string;
  phone_number?: string;
  first_name?: string;
  last_name?: string;
  role: 'super_admin' | 'lottery_manager' | 'payment_verifier' | 'draw_officer' | 'auditor';
  is_active: boolean;
}

export interface Lottery {
  id: string;
  title: string;
  name?: string; // alias
  slug: string;
  description: string;
  ticket_price: string | number;
  total_tickets: number;
  available_tickets_count: number;
  reserved_tickets_count: number;
  sold_tickets_count: number;
  reservation_expiry_hours: number;
  start_date: string;
  draw_date: string;
  status: 'draft' | 'open' | 'paused' | 'closed' | 'drawn';
  first_prize_name?: string;
  first_prize_amount: string | number;
  first_prize_description: string;
  second_prize_name?: string;
  second_prize_amount: string | number;
  second_prize_description: string;
  third_prize_name?: string;
  third_prize_amount: string | number;
  third_prize_description: string;
  payment_accounts?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  lottery: string;
  lottery_title?: string;
  ticket_number: string;
  status: 'available' | 'reserved' | 'sold';
  current_reservation?: {
    id: string;
    customer_phone: string;
    customer_name?: string;
    expires_at: string;
    is_expired: boolean;
  } | null;
  price?: string | number;
  purchased_by?: string;
  purchased_at?: string;
}

export interface Payment {
  id: string;
  reference_number: string;
  amount: string | number;
  payment_method: 'telebirr' | 'cbe' | 'cbe_birr' | 'awash' | 'boa' | 'other';
  status: 'pending' | 'approved' | 'rejected';
  rejection_reason?: string;
  customer_phone: string;
  customer_name?: string;
  telegram_user_id?: string;
  telegram_username?: string;
  receipt_image?: string;
  receipt_url?: string;
  ticket_numbers?: string[];
  lottery_title?: string;
  lottery_id?: string;
  submitted_at: string;
  verified_at?: string;
  verified_by?: string;
  created_at: string;
}

export interface Winner {
  id: string;
  draw: string;
  lottery_title: string;
  ticket_number: string;
  position: 1 | 2 | 3;
  prize_title: string;
  prize_description?: string;
  prize_amount: string | number;
  prize_value?: string | number;
  prize_claimed: boolean;
  claimed_at?: string;
  winner_name?: string;
  winner_phone?: string;
  created_at: string;
}

export interface Draw {
  id: string;
  lottery: string;
  lottery_title: string;
  draw_date: string;
  randomness_hash: string;
  entropy_proof?: string;
  total_eligible_tickets: number;
  winners: Winner[];
  executed_by?: string;
  created_at: string;
}

export interface DashboardMetrics {
  active_lotteries_count: number;
  total_tickets_sold: number;
  pending_payments_count: number;
  today_sales_amount: string | number;
  expiring_reservations_count: number;
  recent_payments?: Payment[];
  active_lotteries?: Lottery[];
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  notification_type: 'payment' | 'draw' | 'reservation' | 'system';
  is_read: boolean;
  created_at: string;
}
