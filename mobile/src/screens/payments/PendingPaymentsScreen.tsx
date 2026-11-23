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
import { Search, Image, CheckCircle, Clock } from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Input } from '../../components/Input';
import { Badge } from '../../components/Badge';
import { EmptyState } from '../../components/EmptyState';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Payment } from '../../types/api';

type TabStatus = 'pending' | 'approved' | 'rejected';

export const PendingPaymentsScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const [activeTab, setActiveTab] = useState<TabStatus>('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPayments = useCallback(async () => {
    try {
      const data = await api.payments.list({
        status: activeTab,
        search: searchQuery.trim() || undefined,
      });
      setPayments(data);
    } catch (e) {
      console.error('Failed to load payments', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [activeTab, searchQuery]);

  useEffect(() => {
    setIsLoading(true);
    fetchPayments();
  }, [fetchPayments]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchPayments();
  };

  const renderPaymentItem = ({ item }: { item: Payment }) => {
    const formattedAmount = Number(item.amount).toLocaleString();
    const dateFormatted = new Date(item.submitted_at || item.created_at).toLocaleDateString(
      undefined,
      {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }
    );

    return (
      <TouchableOpacity
        activeOpacity={0.8}
        style={styles.card}
        onPress={() => navigation.navigate('PaymentDetails', { paymentId: item.id })}
      >
        <View style={styles.cardHeader}>
          <View style={styles.refRow}>
            <Text style={styles.refText}>{item.reference_number}</Text>
            {item.receipt_image && (
              <View style={styles.receiptIndicator}>
                <Image size={13} color={colors.primaryLight} />
                <Text style={styles.receiptText}>Receipt</Text>
              </View>
            )}
          </View>
          <Badge label={item.payment_method} variant={item.payment_method as any} />
        </View>

        <View style={styles.detailsRow}>
          <View>
            <Text style={styles.customerName}>{item.customer_name || 'Customer'}</Text>
            <Text style={styles.customerPhone}>{item.customer_phone}</Text>
          </View>
          <View style={styles.amountBox}>
            <Text style={styles.amountText}>{formattedAmount} ETB</Text>
            <Badge label={item.status} variant={item.status as any} />
          </View>
        </View>

        <View style={styles.footerRow}>
          <View style={styles.dateBox}>
            <Clock size={12} color={colors.textMuted} />
            <Text style={styles.dateText}>{dateFormatted}</Text>
          </View>
          {item.ticket_numbers && item.ticket_numbers.length > 0 && (
            <Text style={styles.ticketCountText}>
              {item.ticket_numbers.length} Ticket{item.ticket_numbers.length > 1 ? 's' : ''} Reserved
            </Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Header
        title="Payment Verification"
        subtitle="Staff Review Queue"
      />

      {/* Tabs */}
      <View style={styles.tabsRow}>
        {(['pending', 'approved', 'rejected'] as TabStatus[]).map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[styles.tab, activeTab === tab ? styles.tabActive : null]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === tab ? styles.tabTextActive : null,
              ]}
            >
              {tab.toUpperCase()}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Search Input */}
      <View style={styles.searchWrapper}>
        <Input
          placeholder="Search by reference code or phone..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          leftIcon={<Search size={16} color={colors.textMuted} />}
          containerStyle={styles.searchInputContainer}
        />
      </View>

      {isLoading ? (
        <LoadingScreen message="Fetching payment records..." />
      ) : (
        <FlatList
          data={payments}
          keyExtractor={(item) => item.id}
          renderItem={renderPaymentItem}
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
              title={`No ${activeTab} payments`}
              message={
                activeTab === 'pending'
                  ? 'All customer transactions have been verified and processed.'
                  : `No ${activeTab} records found matching your filter.`
              }
              icon={<CheckCircle size={36} color={colors.success} />}
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
  tabsRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: colors.primary,
  },
  tabText: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.6,
  },
  tabTextActive: {
    color: colors.primaryLight,
  },
  searchWrapper: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.xs,
  },
  searchInputContainer: {
    marginBottom: 0,
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
  refRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  refText: {
    color: colors.textPrimary,
    fontSize: typography.base,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  receiptIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: colors.primaryMuted,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  receiptText: {
    color: colors.primaryLight,
    fontSize: typography.xs - 2,
    fontWeight: '600',
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  customerName: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '600',
  },
  customerPhone: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
  },
  amountBox: {
    alignItems: 'flex-end',
    gap: 4,
  },
  amountText: {
    color: colors.success,
    fontSize: typography.base,
    fontWeight: '700',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  dateBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  dateText: {
    color: colors.textMuted,
    fontSize: typography.xs,
  },
  ticketCountText: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '500',
  },
});
