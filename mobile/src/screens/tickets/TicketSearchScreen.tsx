import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Search, Ticket as TicketIcon, Clock, Phone } from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Input } from '../../components/Input';
import { Badge } from '../../components/Badge';
import { EmptyState } from '../../components/EmptyState';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Ticket } from '../../types/api';

type TicketFilter = 'all' | 'available' | 'reserved' | 'sold';

export const TicketSearchScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const [filter, setFilter] = useState<TicketFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchTickets = useCallback(async () => {
    try {
      const data = await api.tickets.list({
        status: filter === 'all' ? undefined : filter,
        search: searchQuery.trim() || undefined,
      });
      setTickets(data);
    } catch (e) {
      console.error('Failed to load tickets', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [filter, searchQuery]);

  useEffect(() => {
    setIsLoading(true);
    fetchTickets();
  }, [fetchTickets]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchTickets();
  };

  const renderTicketItem = ({ item }: { item: Ticket }) => {
    const reservation = item.current_reservation;

    return (
      <TouchableOpacity
        activeOpacity={0.8}
        style={styles.card}
        onPress={() => navigation.navigate('TicketDetails', { ticketId: item.id })}
      >
        <View style={styles.cardLeft}>
          <View style={styles.numberBadge}>
            <Text style={styles.numberText}>#{item.ticket_number}</Text>
          </View>
          <View style={styles.ticketMeta}>
            <Text style={styles.lotteryTitle} numberOfLines={1}>
              {item.lottery_title || 'Lottery Entry'}
            </Text>
            {reservation?.customer_phone && (
              <View style={styles.phoneRow}>
                <Phone size={11} color={colors.textSecondary} />
                <Text style={styles.phoneText}>{reservation.customer_phone}</Text>
              </View>
            )}
            {item.purchased_by && (
              <View style={styles.phoneRow}>
                <Phone size={11} color={colors.success} />
                <Text style={styles.phoneText}>Sold to: {item.purchased_by}</Text>
              </View>
            )}
          </View>
        </View>

        <View style={styles.cardRight}>
          <Badge label={item.status} variant={item.status as any} />
          {reservation && (
            <View style={styles.expiryRow}>
              <Clock size={11} color={colors.warning} />
              <Text style={styles.expiryText}>
                {new Date(reservation.expires_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Header title="Ticket Search" subtitle="Find tickets by number or phone" />

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {(['all', 'available', 'reserved', 'sold'] as TicketFilter[]).map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.filterChip, filter === f ? styles.filterChipActive : null]}
            onPress={() => setFilter(f)}
          >
            <Text style={[styles.filterText, filter === f ? styles.filterTextActive : null]}>
              {f.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Search Input */}
      <View style={styles.searchWrapper}>
        <Input
          placeholder="Search ticket number (e.g. 0042) or phone..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          leftIcon={<Search size={16} color={colors.textMuted} />}
          containerStyle={styles.searchContainer}
        />
      </View>

      {isLoading ? (
        <LoadingScreen message="Searching tickets..." />
      ) : (
        <FlatList
          data={tickets}
          keyExtractor={(item) => item.id}
          renderItem={renderTicketItem}
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
              title="No tickets found"
              message="Try adjusting your ticket number or status filter."
              icon={<TicketIcon size={36} color={colors.textMuted} />}
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
  searchWrapper: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xs,
  },
  searchContainer: {
    marginBottom: 0,
  },
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xxxl,
  },
  card: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: spacing.md,
  },
  numberBadge: {
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.sm,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  numberText: {
    color: colors.textPrimary,
    fontSize: typography.base,
    fontWeight: '800',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  ticketMeta: {
    flex: 1,
  },
  lotteryTitle: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '600',
  },
  phoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 2,
  },
  phoneText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  cardRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  expiryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  expiryText: {
    color: colors.warning,
    fontSize: typography.xs - 2,
  },
});
