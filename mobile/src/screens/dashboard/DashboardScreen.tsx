import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import {
  Ticket,
  Clock,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Search,
  Trophy,
  ArrowRight,
  Shield,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { StatCard } from '../../components/StatCard';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { LoadingScreen } from '../../components/LoadingScreen';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/endpoints';
import { DashboardMetrics, Payment } from '../../types/api';

export const DashboardScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { user } = useAuth();

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await api.dashboard.getMetrics();
      setMetrics(data);

      // Also fetch top pending payments
      const payments = await api.payments.list({ status: 'pending' });
      setRecentPayments(payments.slice(0, 3));
    } catch (e) {
      console.error('Error fetching dashboard metrics', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  if (isLoading && !metrics) {
    return <LoadingScreen message="Loading dashboard metrics..." />;
  }

  const pendingCount = metrics?.pending_payments_count || 0;
  const activeLotteries = metrics?.active_lotteries_count || 0;
  const ticketsSold = metrics?.total_tickets_sold || 0;
  const todaySales = metrics?.today_sales_amount || '0.00';
  const expiringCount = metrics?.expiring_reservations_count || 0;

  return (
    <View style={styles.container}>
      <Header
        title="Operations Control"
        subtitle={`Staff: ${user?.first_name || user?.email || 'Officer'}`}
        onNotifications={() => navigation.navigate('Notifications')}
      />

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        {/* Role banner */}
        <View style={styles.roleBanner}>
          <Shield size={16} color={colors.primaryLight} />
          <Text style={styles.roleText}>
            Role: <Text style={styles.roleHighlight}>{user?.role?.replace('_', ' ').toUpperCase()}</Text>
          </Text>
        </View>

        {/* Urgent Action Banner: Pending Payments */}
        {pendingCount > 0 && (
          <View style={styles.urgentBanner}>
            <View style={styles.urgentLeft}>
              <View style={styles.urgentIcon}>
                <AlertTriangle size={20} color={colors.warning} />
              </View>
              <View>
                <Text style={styles.urgentTitle}>
                  {pendingCount} Payment{pendingCount > 1 ? 's' : ''} Pending Verification
                </Text>
                <Text style={styles.urgentSubtitle}>
                  Manual bank statement confirmation required
                </Text>
              </View>
            </View>
            <Button
              title="Review"
              size="sm"
              variant="primary"
              onPress={() => navigation.navigate('Payments')}
              style={styles.urgentBtn}
            />
          </View>
        )}

        {/* KPI Grid */}
        <Text style={styles.sectionHeading}>KEY OPERATIONAL METRICS</Text>
        <View style={styles.kpiGrid}>
          <StatCard
            title="Active Lotteries"
            value={activeLotteries}
            subtitle="Currently accepting entries"
            icon={<Ticket size={20} color={colors.primaryLight} />}
            accentColor={colors.primary}
            onPress={() => navigation.navigate('Lotteries')}
            style={styles.kpiCard}
          />

          <StatCard
            title="Tickets Sold"
            value={ticketsSold.toLocaleString()}
            subtitle="Confirmed valid entries"
            icon={<CheckCircle size={20} color={colors.success} />}
            accentColor={colors.success}
            onPress={() => navigation.navigate('Tickets')}
            style={styles.kpiCard}
          />

          <StatCard
            title="Today's Sales"
            value={`${Number(todaySales).toLocaleString()} ETB`}
            subtitle="Approved transactions today"
            icon={<TrendingUp size={20} color={colors.info} />}
            accentColor={colors.info}
            style={styles.kpiCard}
          />

          <StatCard
            title="Expiring Soon"
            value={expiringCount}
            subtitle="Reservations < 2 hrs to expire"
            icon={<Clock size={20} color={colors.warning} />}
            accentColor={colors.warning}
            style={styles.kpiCard}
          />
        </View>

        {/* Quick Action Hub */}
        <Text style={styles.sectionHeading}>QUICK ACTIONS</Text>
        <View style={styles.quickActionGrid}>
          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('Payments')}
          >
            <View style={[styles.actionIcon, { backgroundColor: colors.warningLight }]}>
              <CheckCircle size={22} color={colors.warning} />
            </View>
            <Text style={styles.actionTitle}>Review Queue</Text>
            <Text style={styles.actionDesc}>Inspect bank references & receipts</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('Tickets')}
          >
            <View style={[styles.actionIcon, { backgroundColor: colors.infoLight }]}>
              <Search size={22} color={colors.info} />
            </View>
            <Text style={styles.actionTitle}>Ticket Search</Text>
            <Text style={styles.actionDesc}>Look up by number or customer</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('Lotteries')}
          >
            <View style={[styles.actionIcon, { backgroundColor: colors.primaryMuted }]}>
              <Ticket size={22} color={colors.primaryLight} />
            </View>
            <Text style={styles.actionTitle}>Lotteries</Text>
            <Text style={styles.actionDesc}>Monitor ticket capacities & draw dates</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionTile}
            onPress={() => navigation.navigate('Winners')}
          >
            <View style={[styles.actionIcon, { backgroundColor: colors.goldMuted }]}>
              <Trophy size={22} color={colors.gold} />
            </View>
            <Text style={styles.actionTitle}>Winners & Proofs</Text>
            <Text style={styles.actionDesc}>SHA-256 entropy & prize claims</Text>
          </TouchableOpacity>
        </View>

        {/* Pending Review Preview */}
        {recentPayments.length > 0 && (
          <View style={styles.recentSection}>
            <View style={styles.recentHeader}>
              <Text style={styles.sectionHeading}>NEEDS VERIFICATION</Text>
              <TouchableOpacity onPress={() => navigation.navigate('Payments')}>
                <View style={styles.viewAllRow}>
                  <Text style={styles.viewAllText}>View All</Text>
                  <ArrowRight size={14} color={colors.primaryLight} />
                </View>
              </TouchableOpacity>
            </View>

            {recentPayments.map((p) => (
              <TouchableOpacity
                key={p.id}
                style={styles.paymentPreviewCard}
                onPress={() => navigation.navigate('PaymentDetails', { paymentId: p.id })}
              >
                <View style={styles.previewTop}>
                  <Text style={styles.previewRef}>REF: {p.reference_number}</Text>
                  <Badge label={p.payment_method} variant={p.payment_method as any} />
                </View>

                <View style={styles.previewBottom}>
                  <Text style={styles.previewPhone}>{p.customer_phone || 'Customer'}</Text>
                  <Text style={styles.previewAmount}>
                    {Number(p.amount).toLocaleString()} ETB
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
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
  roleBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    marginBottom: spacing.md,
    alignSelf: 'flex-start',
  },
  roleText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  roleHighlight: {
    color: colors.primaryLight,
    fontWeight: '700',
  },
  urgentBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: colors.warning,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  urgentLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: spacing.sm,
  },
  urgentIcon: {
    marginRight: spacing.sm,
  },
  urgentTitle: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
  },
  urgentSubtitle: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
  },
  urgentBtn: {
    alignSelf: 'center',
  },
  sectionHeading: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: spacing.sm,
    marginTop: spacing.xs,
  },
  kpiGrid: {
    marginBottom: spacing.md,
  },
  kpiCard: {
    marginBottom: spacing.sm,
  },
  quickActionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  actionTile: {
    width: '48%',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  actionIcon: {
    width: 42,
    height: 42,
    borderRadius: borderRadius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  actionTitle: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
  },
  actionDesc: {
    color: colors.textMuted,
    fontSize: typography.xs,
    marginTop: 2,
  },
  recentSection: {
    marginTop: spacing.sm,
  },
  recentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  viewAllRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  viewAllText: {
    color: colors.primaryLight,
    fontSize: typography.xs,
    fontWeight: '600',
  },
  paymentPreviewCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  previewTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  previewRef: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  previewBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  previewPhone: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  previewAmount: {
    color: colors.success,
    fontSize: typography.sm,
    fontWeight: '700',
  },
});
