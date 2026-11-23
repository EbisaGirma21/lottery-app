import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import {
  Trophy,
  Calendar,
  Clock,
  Ticket,
  DollarSign,
  CreditCard,
  Search,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Lottery } from '../../types/api';

export const LotteryDetailsScreen: React.FC = () => {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { lotteryId } = route.params;

  const [lottery, setLottery] = useState<Lottery | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchLottery = useCallback(async () => {
    try {
      const data = await api.lotteries.getById(lotteryId);
      setLottery(data);
    } catch (e) {
      console.error('Failed to load lottery detail', e);
      Alert.alert('Error', 'Unable to load lottery details.');
    } finally {
      setIsLoading(false);
    }
  }, [lotteryId]);

  useEffect(() => {
    fetchLottery();
  }, [fetchLottery]);

  if (isLoading || !lottery) {
    return <LoadingScreen message="Loading lottery metadata..." />;
  }

  const firstPrize = Number(lottery.first_prize_amount).toLocaleString();
  const secondPrize = Number(lottery.second_prize_amount).toLocaleString();
  const thirdPrize = Number(lottery.third_prize_amount).toLocaleString();
  const ticketPrice = Number(lottery.ticket_price).toLocaleString();

  return (
    <View style={styles.container}>
      <Header
        title={lottery.title || lottery.name || 'Lottery Details'}
        subtitle={`Status: ${lottery.status.toUpperCase()}`}
        onBack={() => navigation.goBack()}
      />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Basic Info Card */}
        <View style={styles.card}>
          <View style={styles.cardTop}>
            <Text style={styles.title}>{lottery.title || lottery.name}</Text>
            <Badge label={lottery.status} variant={lottery.status as any} size="md" />
          </View>

          {lottery.description ? (
            <Text style={styles.description}>{lottery.description}</Text>
          ) : null}

          <View style={styles.infoRow}>
            <View style={styles.infoItem}>
              <DollarSign size={16} color={colors.success} />
              <View>
                <Text style={styles.infoLabel}>Ticket Price</Text>
                <Text style={styles.infoValue}>{ticketPrice} ETB</Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Clock size={16} color={colors.warning} />
              <View>
                <Text style={styles.infoLabel}>Reservation Window</Text>
                <Text style={styles.infoValue}>
                  {lottery.reservation_expiry_hours || 48} Hours
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.infoRow}>
            <View style={styles.infoItem}>
              <Calendar size={16} color={colors.info} />
              <View>
                <Text style={styles.infoLabel}>Draw Scheduled</Text>
                <Text style={styles.infoValue}>
                  {new Date(lottery.draw_date).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* 3 Winning Positions Card */}
        <View style={styles.card}>
          <Text style={styles.cardHeading}>3 OFFICIAL WINNING POSITIONS</Text>

          {/* 1st Prize */}
          <View style={[styles.prizeItem, { borderColor: 'rgba(251, 191, 36, 0.4)' }]}>
            <View style={[styles.medalCircle, { backgroundColor: colors.goldMuted }]}>
              <Trophy size={20} color={colors.gold} />
            </View>
            <View style={styles.prizeDetails}>
              <View style={styles.prizeTitleRow}>
                <Text style={[styles.medalLabel, { color: colors.gold }]}>1ST POSITION</Text>
                <Text style={styles.prizeValue}>{firstPrize} ETB</Text>
              </View>
              <Text style={styles.prizeDesc}>
                {lottery.first_prize_description || 'First Place Jackpot Winner'}
              </Text>
            </View>
          </View>

          {/* 2nd Prize */}
          <View style={[styles.prizeItem, { borderColor: 'rgba(156, 163, 175, 0.3)' }]}>
            <View style={[styles.medalCircle, { backgroundColor: colors.silverMuted }]}>
              <Trophy size={20} color={colors.silver} />
            </View>
            <View style={styles.prizeDetails}>
              <View style={styles.prizeTitleRow}>
                <Text style={[styles.medalLabel, { color: colors.silver }]}>2ND POSITION</Text>
                <Text style={styles.prizeValue}>{secondPrize} ETB</Text>
              </View>
              <Text style={styles.prizeDesc}>
                {lottery.second_prize_description || 'Second Place Winner'}
              </Text>
            </View>
          </View>

          {/* 3rd Prize */}
          <View style={[styles.prizeItem, { borderColor: 'rgba(217, 119, 6, 0.3)' }]}>
            <View style={[styles.medalCircle, { backgroundColor: colors.bronzeMuted }]}>
              <Trophy size={20} color={colors.bronze} />
            </View>
            <View style={styles.prizeDetails}>
              <View style={styles.prizeTitleRow}>
                <Text style={[styles.medalLabel, { color: colors.bronze }]}>3RD POSITION</Text>
                <Text style={styles.prizeValue}>{thirdPrize} ETB</Text>
              </View>
              <Text style={styles.prizeDesc}>
                {lottery.third_prize_description || 'Third Place Winner'}
              </Text>
            </View>
          </View>
        </View>

        {/* Dynamic Ticket Capacity Metrics */}
        <View style={styles.card}>
          <Text style={styles.cardHeading}>TICKET INVENTORY</Text>

          <View style={styles.statsGrid}>
            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Total Capacity</Text>
              <Text style={styles.statBoxValue}>{lottery.total_tickets}</Text>
            </View>

            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Available</Text>
              <Text style={[styles.statBoxValue, { color: colors.info }]}>
                {lottery.available_tickets_count ||
                  lottery.total_tickets -
                    ((lottery.sold_tickets_count || 0) + (lottery.reserved_tickets_count || 0))}
              </Text>
            </View>

            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Reserved</Text>
              <Text style={[styles.statBoxValue, { color: colors.warning }]}>
                {lottery.reserved_tickets_count || 0}
              </Text>
            </View>

            <View style={styles.statBox}>
              <Text style={styles.statBoxLabel}>Sold / Confirmed</Text>
              <Text style={[styles.statBoxValue, { color: colors.success }]}>
                {lottery.sold_tickets_count || 0}
              </Text>
            </View>
          </View>
        </View>

        {/* Accepted Payment Channels */}
        {lottery.payment_accounts && Object.keys(lottery.payment_accounts).length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardHeading}>ACCEPTED PAYMENT CHANNELS</Text>
            {Object.entries(lottery.payment_accounts).map(([channel, account]) => (
              <View key={channel} style={styles.paymentAccountRow}>
                <CreditCard size={16} color={colors.primaryLight} />
                <Text style={styles.channelName}>{channel.toUpperCase()}:</Text>
                <Text style={styles.accountNumber}>{String(account)}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Shortcuts */}
        <View style={styles.actionsBox}>
          <Button
            title="Search Tickets in this Lottery"
            variant="outline"
            onPress={() => navigation.navigate('Tickets')}
            icon={<Search size={16} color={colors.primaryLight} />}
            style={styles.actionBtn}
          />
        </View>
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
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.textPrimary,
    fontSize: typography.lg,
    fontWeight: '700',
    flex: 1,
    marginRight: spacing.sm,
  },
  description: {
    color: colors.textSecondary,
    fontSize: typography.sm,
    marginBottom: spacing.md,
    lineHeight: 20,
  },
  infoRow: {
    flexDirection: 'row',
    gap: spacing.lg,
    marginTop: spacing.xs,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  infoLabel: {
    color: colors.textMuted,
    fontSize: typography.xs - 2,
    textTransform: 'uppercase',
  },
  infoValue: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '600',
    marginTop: 1,
  },
  cardHeading: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: spacing.md,
  },
  prizeItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginBottom: spacing.sm,
    gap: spacing.sm,
  },
  medalCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  prizeDetails: {
    flex: 1,
  },
  prizeTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  medalLabel: {
    fontSize: typography.xs,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  prizeValue: {
    color: colors.textPrimary,
    fontSize: typography.base,
    fontWeight: '800',
  },
  prizeDesc: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  statBox: {
    width: '48%',
    backgroundColor: colors.surfaceLight,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statBoxLabel: {
    color: colors.textMuted,
    fontSize: typography.xs - 1,
  },
  statBoxValue: {
    color: colors.textPrimary,
    fontSize: typography.lg,
    fontWeight: '700',
    marginTop: 2,
  },
  paymentAccountRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  channelName: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  accountNumber: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    fontFamily: 'monospace',
  },
  actionsBox: {
    marginTop: spacing.sm,
  },
  actionBtn: {
    width: '100%',
  },
});
