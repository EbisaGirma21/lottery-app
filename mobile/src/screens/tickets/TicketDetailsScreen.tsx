import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Platform,
  Alert,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import {
  Ticket as TicketIcon,
  Clock,
  User,
  Calendar,
  DollarSign,
  ShieldCheck,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Ticket } from '../../types/api';

export const TicketDetailsScreen: React.FC = () => {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { ticketId } = route.params;

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTicket = useCallback(async () => {
    try {
      const data = await api.tickets.getById(ticketId);
      setTicket(data);
    } catch (e) {
      console.error('Failed to load ticket detail', e);
      Alert.alert('Error', 'Unable to retrieve ticket information.');
    } finally {
      setIsLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  if (isLoading || !ticket) {
    return <LoadingScreen message="Loading ticket details..." />;
  }

  const reservation = ticket.current_reservation;

  return (
    <View style={styles.container}>
      <Header
        title={`Ticket #${ticket.ticket_number}`}
        subtitle={ticket.lottery_title || 'Lottery Entry'}
        onBack={() => navigation.goBack()}
      />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Big Ticket Presentation Card */}
        <View style={styles.ticketCard}>
          <View style={styles.ticketHeader}>
            <Text style={styles.lotteryName}>{ticket.lottery_title || 'Lottery Entry'}</Text>
            <Badge label={ticket.status} variant={ticket.status as any} size="md" />
          </View>

          <View style={styles.numberContainer}>
            <Text style={styles.numberLabel}>TICKET NUMBER</Text>
            <Text style={styles.bigNumber}>#{ticket.ticket_number}</Text>
          </View>

          <View style={styles.divider} />

          <View style={styles.ticketFooter}>
            <View style={styles.inlineItem}>
              <DollarSign size={16} color={colors.success} />
              <Text style={styles.footerText}>
                Price: {ticket.price ? `${ticket.price} ETB` : 'Standard'}
              </Text>
            </View>
            <View style={styles.inlineItem}>
              <ShieldCheck size={16} color={colors.primaryLight} />
              <Text style={styles.footerText}>Official Entry</Text>
            </View>
          </View>
        </View>

        {/* Reservation Details (If Reserved) */}
        {reservation && (
          <View style={styles.card}>
            <Text style={styles.cardHeading}>ACTIVE RESERVATION DETAILS</Text>

            <View style={styles.row}>
              <Text style={styles.label}>Customer Phone:</Text>
              <Text style={styles.value}>{reservation.customer_phone}</Text>
            </View>

            {reservation.customer_name && (
              <View style={styles.row}>
                <Text style={styles.label}>Customer Name:</Text>
                <Text style={styles.value}>{reservation.customer_name}</Text>
              </View>
            )}

            <View style={styles.row}>
              <Text style={styles.label}>Expires At:</Text>
              <View style={styles.inlineItem}>
                <Clock size={14} color={colors.warning} />
                <Text style={[styles.value, { color: colors.warning }]}>
                  {new Date(reservation.expires_at).toLocaleString()}
                </Text>
              </View>
            </View>

            <View style={styles.row}>
              <Text style={styles.label}>Reservation Status:</Text>
              <Badge
                label={reservation.is_expired ? 'Expired' : 'Active 48h Window'}
                variant={reservation.is_expired ? 'rejected' : 'pending'}
              />
            </View>
          </View>
        )}

        {/* Ownership / Sale Details (If Sold) */}
        {ticket.status === 'sold' && (
          <View style={styles.card}>
            <Text style={styles.cardHeading}>CONFIRMED SALE RECORD</Text>

            {ticket.purchased_by && (
              <View style={styles.row}>
                <Text style={styles.label}>Purchased By:</Text>
                <View style={styles.inlineItem}>
                  <User size={14} color={colors.success} />
                  <Text style={styles.value}>{ticket.purchased_by}</Text>
                </View>
              </View>
            )}

            {ticket.purchased_at && (
              <View style={styles.row}>
                <Text style={styles.label}>Purchase Timestamp:</Text>
                <View style={styles.inlineItem}>
                  <Calendar size={14} color={colors.textMuted} />
                  <Text style={styles.value}>
                    {new Date(ticket.purchased_at).toLocaleString()}
                  </Text>
                </View>
              </View>
            )}
          </View>
        )}

        {/* If Available */}
        {ticket.status === 'available' && (
          <View style={styles.card}>
            <Text style={styles.cardHeading}>STATUS INFO</Text>
            <Text style={styles.availableText}>
              This ticket is currently unreserved and available for customer purchase through the
              Telegram bot.
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xxxl,
  },
  ticketCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    marginBottom: spacing.md,
    alignItems: 'center',
    shadowColor: colors.primary,
    shadowOpacity: 0.15,
    shadowRadius: 12,
  },
  ticketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: spacing.lg,
  },
  lotteryName: {
    color: colors.textSecondary,
    fontSize: typography.sm,
    fontWeight: '600',
    flex: 1,
  },
  numberContainer: {
    alignItems: 'center',
    marginVertical: spacing.md,
  },
  numberLabel: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 4,
  },
  bigNumber: {
    color: colors.textPrimary,
    fontSize: typography.title + 8,
    fontWeight: '900',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  divider: {
    width: '100%',
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.md,
  },
  ticketFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  inlineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  footerText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    fontWeight: '600',
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  cardHeading: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: spacing.md,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs + 2,
  },
  label: {
    color: colors.textSecondary,
    fontSize: typography.sm,
  },
  value: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '600',
  },
  availableText: {
    color: colors.textSecondary,
    fontSize: typography.sm,
    lineHeight: 20,
  },
});
