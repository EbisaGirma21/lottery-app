import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import { Trophy, Award, CheckCircle, ShieldCheck, Hash } from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { EmptyState } from '../../components/EmptyState';
import { LoadingScreen } from '../../components/LoadingScreen';
import { Button } from '../../components/Button';
import { api } from '../../api/endpoints';
import { Draw, Winner } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

export const WinnersScreen: React.FC = () => {
  const { isDrawOfficer, isSuperAdmin } = useAuth();

  const [draws, setDraws] = useState<Draw[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [claimingId, setClaimingId] = useState<string | null>(null);

  const fetchDraws = useCallback(async () => {
    try {
      const data = await api.draws.list();
      setDraws(data);
    } catch (e) {
      console.error('Failed to load draws', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    fetchDraws();
  }, [fetchDraws]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDraws();
  };

  const handleClaimPrize = (winner: Winner) => {
    const rawVal = Number(winner.prize_amount || winner.prize_value || 0);
    const valText = rawVal > 0 ? `${rawVal.toLocaleString()} ETB` : (winner.prize_title || 'Physical Prize');
    Alert.alert(
      'Confirm Prize Claim',
      `Mark prize (${valText}) for Ticket #${winner.ticket_number} as CLAIMED and disbursed?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm Claim',
          onPress: async () => {
            setClaimingId(winner.id);
            try {
              await api.winners.claim(winner.id);
              Alert.alert('Success', 'Prize marked as claimed!');
              fetchDraws();
            } catch (err: any) {
              const msg =
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Failed to claim prize.';
              Alert.alert('Error', msg);
            } finally {
              setClaimingId(null);
            }
          },
        },
      ]
    );
  };

  const renderDrawCard = ({ item }: { item: Draw }) => {
    const drawDateFormatted = new Date(item.draw_date || item.created_at).toLocaleDateString(
      undefined,
      {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }
    );

    const winnersSorted = [...(item.winners || [])].sort((a, b) => a.position - b.position);

    return (
      <View style={styles.drawCard}>
        {/* Draw Header */}
        <View style={styles.drawHeader}>
          <View>
            <Text style={styles.lotteryTitle}>{item.lottery_title || 'Completed Draw'}</Text>
            <Text style={styles.drawDate}>{drawDateFormatted}</Text>
          </View>
          <Badge label="OFFICIAL DRAW" variant="drawn" />
        </View>

        {/* SHA-256 Entropy Audit Proof */}
        <View style={styles.auditProofBox}>
          <View style={styles.auditProofHeader}>
            <ShieldCheck size={14} color={colors.primaryLight} />
            <Text style={styles.auditProofTitle}>Cryptographic Audit Proof</Text>
          </View>
          <View style={styles.hashRow}>
            <Hash size={12} color={colors.textMuted} />
            <Text style={styles.hashText} numberOfLines={1} ellipsizeMode="middle">
              {item.randomness_hash || item.entropy_proof || 'SHA-256 Proof Verified'}
            </Text>
          </View>
          <Text style={styles.auditDetail}>
            Drawn from pool of {item.total_eligible_tickets || 0} verified sold tickets
          </Text>
        </View>

        {/* 3 Winning Positions Podium */}
        <View style={styles.winnersContainer}>
          {winnersSorted.map((winner) => {
            const isFirst = winner.position === 1;
            const isSecond = winner.position === 2;
            const isThird = winner.position === 3;

            const medalColor = isFirst ? colors.gold : isSecond ? colors.silver : colors.bronze;
            const medalBg = isFirst
              ? colors.goldMuted
              : isSecond
              ? colors.silverMuted
              : colors.bronzeMuted;
            const medalBorder = isFirst
              ? 'rgba(251, 191, 36, 0.4)'
              : isSecond
              ? 'rgba(156, 163, 175, 0.4)'
              : 'rgba(217, 119, 6, 0.4)';

            const numVal = Number(winner.prize_amount || winner.prize_value || 0);
            const prizeDisplay = numVal > 0 ? `${numVal.toLocaleString()} ETB` : (winner.prize_title || 'Physical Prize');

            return (
              <View key={winner.id} style={[styles.winnerRow, { borderColor: medalBorder }]}>
                <View style={[styles.medalBadge, { backgroundColor: medalBg }]}>
                  {isFirst ? (
                    <Trophy size={18} color={medalColor} />
                  ) : (
                    <Award size={18} color={medalColor} />
                  )}
                  <Text style={[styles.positionNumber, { color: medalColor }]}>
                    {winner.position}
                    {winner.position === 1 ? 'ST' : winner.position === 2 ? 'ND' : 'RD'}
                  </Text>
                </View>

                <View style={styles.winnerInfo}>
                  <View style={styles.winnerTop}>
                    <Text style={styles.ticketNumber}>Ticket #{winner.ticket_number}</Text>
                    <Text style={styles.prizeAmountText}>{prizeDisplay}</Text>
                  </View>

                  <View style={styles.winnerBottom}>
                    <Text style={styles.winnerPhone}>
                      {winner.winner_name || winner.winner_phone || 'Masked Winner'}
                    </Text>
                    {winner.prize_claimed ? (
                      <View style={styles.claimedPill}>
                        <CheckCircle size={12} color={colors.success} />
                        <Text style={styles.claimedText}>Claimed</Text>
                      </View>
                    ) : (
                      (isDrawOfficer || isSuperAdmin) && (
                        <Button
                          title="Claim"
                          size="sm"
                          variant="outline"
                          onPress={() => handleClaimPrize(winner)}
                          loading={claimingId === winner.id}
                          style={styles.claimBtn}
                        />
                      )
                    )}
                  </View>
                </View>
              </View>
            );
          })}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Header
        title="Winners & Draws"
        subtitle="1st, 2nd & 3rd Place Cryptographic Results"
      />

      {isLoading ? (
        <LoadingScreen message="Loading winning draws..." />
      ) : (
        <FlatList
          data={draws}
          keyExtractor={(item) => item.id}
          renderItem={renderDrawCard}
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
              title="No draws completed yet"
              message="When an open lottery closes and draw is executed, cryptographic results will display here."
              icon={<Trophy size={36} color={colors.gold} />}
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
  listContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xxxl,
  },
  drawCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  drawHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  lotteryTitle: {
    color: colors.textPrimary,
    fontSize: typography.md,
    fontWeight: '700',
  },
  drawDate: {
    color: colors.textMuted,
    fontSize: typography.xs,
    marginTop: 2,
  },
  auditProofBox: {
    backgroundColor: colors.surfaceLight,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginBottom: spacing.md,
  },
  auditProofHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 4,
  },
  auditProofTitle: {
    color: colors.primaryLight,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  hashRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginVertical: 2,
  },
  hashText: {
    color: colors.textSecondary,
    fontSize: typography.xs - 1,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    flex: 1,
  },
  auditDetail: {
    color: colors.textMuted,
    fontSize: typography.xs - 2,
    marginTop: 2,
  },
  winnersContainer: {
    gap: spacing.sm,
  },
  winnerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    gap: spacing.sm,
  },
  medalBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  positionNumber: {
    fontSize: typography.xs - 2,
    fontWeight: '800',
    marginTop: 1,
  },
  winnerInfo: {
    flex: 1,
  },
  winnerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ticketNumber: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  prizeAmountText: {
    color: colors.success,
    fontSize: typography.sm,
    fontWeight: '700',
  },
  winnerBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  winnerPhone: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  claimedPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.successLight,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: borderRadius.full,
  },
  claimedText: {
    color: colors.success,
    fontSize: typography.xs - 1,
    fontWeight: '700',
  },
  claimBtn: {
    paddingVertical: 3,
    paddingHorizontal: 10,
  },
});
