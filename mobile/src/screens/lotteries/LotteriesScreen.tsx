import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Trophy, Calendar, Ticket, ArrowRight } from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { EmptyState } from '../../components/EmptyState';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Lottery } from '../../types/api';

type LotteryFilter = 'all' | 'open' | 'closed' | 'drawn' | 'paused';

export const LotteriesScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const [activeFilter, setActiveFilter] = useState<LotteryFilter>('all');
  const [lotteries, setLotteries] = useState<Lottery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchLotteries = useCallback(async () => {
    try {
      const data = await api.lotteries.list({
        status: activeFilter === 'all' ? undefined : activeFilter,
      });
      setLotteries(data);
    } catch (e) {
      console.error('Failed to load lotteries', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [activeFilter]);

  useEffect(() => {
    setIsLoading(true);
    fetchLotteries();
  }, [fetchLotteries]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchLotteries();
  };

  const renderLotteryCard = ({ item }: { item: Lottery }) => {
    const total = item.total_tickets || 1;
    const sold = item.sold_tickets_count || 0;
    const reserved = item.reserved_tickets_count || 0;
    const progress = Math.min(100, Math.round(((sold + reserved) / total) * 100));

    const drawDateFormatted = new Date(item.draw_date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

    const firstPrizeFormatted = Number(item.first_prize_amount).toLocaleString();
    const ticketPriceFormatted = Number(item.ticket_price).toLocaleString();

    return (
      <TouchableOpacity
        activeOpacity={0.8}
        style={styles.card}
        onPress={() => navigation.navigate('LotteryDetails', { lotteryId: item.id })}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.title} numberOfLines={1}>
            {item.title || item.name || 'Lottery'}
          </Text>
          <Badge label={item.status} variant={item.status as any} />
        </View>

        {/* 1st Prize Highlight */}
        <View style={styles.prizeBox}>
          <View style={styles.prizeIcon}>
            <Trophy size={18} color={colors.gold} />
          </View>
          <View>
            <Text style={styles.prizeLabel}>1ST GRAND PRIZE</Text>
            <Text style={styles.prizeAmount}>{firstPrizeFormatted} ETB</Text>
          </View>
        </View>

        {/* Ticket Capacity Progress Bar */}
        <View style={styles.capacitySection}>
          <View style={styles.capacityLabels}>
            <Text style={styles.capacityText}>
              Sold: {sold} / {total}
            </Text>
            <Text style={styles.capacityPercent}>{progress}%</Text>
          </View>
          <View style={styles.progressBarTrack}>
            <View
              style={[
                styles.progressBarFill,
                { width: `${progress}%` },
                progress > 80 ? { backgroundColor: colors.warning } : null,
              ]}
            />
          </View>
        </View>

        {/* Footer info */}
        <View style={styles.footer}>
          <View style={styles.footerCol}>
            <Text style={styles.footerLabel}>Price / Ticket</Text>
            <Text style={styles.priceValue}>{ticketPriceFormatted} ETB</Text>
          </View>

          <View style={styles.footerCol}>
            <Text style={styles.footerLabel}>Draw Date</Text>
            <View style={styles.dateRow}>
              <Calendar size={12} color={colors.textMuted} />
              <Text style={styles.dateValue}>{drawDateFormatted}</Text>
            </View>
          </View>

          <View style={styles.arrowBox}>
            <ArrowRight size={16} color={colors.primaryLight} />
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Header title="Lottery Management" subtitle="Dynamic Ticket Capacity" />

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {(['all', 'open', 'closed', 'drawn', 'paused'] as LotteryFilter[]).map((filter) => (
          <TouchableOpacity
            key={filter}
            style={[styles.filterChip, activeFilter === filter ? styles.filterChipActive : null]}
            onPress={() => setActiveFilter(filter)}
          >
            <Text
              style={[
                styles.filterText,
                activeFilter === filter ? styles.filterTextActive : null,
              ]}
            >
              {filter.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {isLoading ? (
        <LoadingScreen message="Loading lotteries..." />
      ) : (
        <FlatList
          data={lotteries}
          keyExtractor={(item) => item.id}
          renderItem={renderLotteryCard}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.primary}
            />
          }
          ListEmptyComponent={
            <EmptyState
              title="No lotteries found"
              message={`No lotteries match the current filter "${activeFilter}".`}
              icon={<Ticket size={36} color={colors.primaryLight} />}
            />
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    gap: spacing.xs,
  },
  filterChip: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.full,
    backgroundColor: colors.surfaceLight,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
  },
  filterText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  filterTextActive: {
    color: '#FFFFFF',
  },
  listContent: {
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
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  title: {
    color: colors.textPrimary,
    fontSize: typography.md,
    fontWeight: '700',
    flex: 1,
    marginRight: spacing.sm,
  },
  prizeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.goldMuted,
    borderColor: 'rgba(251, 191, 36, 0.25)',
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  prizeIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(251, 191, 36, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  prizeLabel: {
    color: colors.gold,
    fontSize: typography.xs - 2,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  prizeAmount: {
    color: '#FFFFFF',
    fontSize: typography.base,
    fontWeight: '800',
  },
  capacitySection: {
    marginBottom: spacing.md,
  },
  capacityLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  capacityText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  capacityPercent: {
    color: colors.primaryLight,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  progressBarTrack: {
    height: 6,
    backgroundColor: colors.surfaceLight,
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 3,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 255, 255, 0.05)',
  },
  footerCol: {
    flex: 1,
  },
  footerLabel: {
    color: colors.textMuted,
    fontSize: typography.xs - 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  priceValue: {
    color: colors.success,
    fontSize: typography.sm,
    fontWeight: '700',
    marginTop: 2,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  dateValue: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  arrowBox: {
    padding: spacing.xs,
  },
});
