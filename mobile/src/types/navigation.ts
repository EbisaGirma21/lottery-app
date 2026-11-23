/**
 * React Navigation Screen & Param Types
 */

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  PaymentDetails: { paymentId: string };
  LotteryDetails: { lotteryId: string };
  TicketDetails: { ticketId: string };
  Notifications: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  Payments: undefined;
  Lotteries: undefined;
  Tickets: undefined;
  Winners: undefined;
  Profile: undefined;
};
