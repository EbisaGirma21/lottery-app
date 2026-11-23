import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Modal,
  Alert,
  Platform,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import {
  AlertCircle,
  CheckCircle,
  XCircle,
  Maximize2,
  X,
  Phone,
  Calendar,
  Ticket,
  ShieldAlert,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { Payment } from '../../types/api';
import { useAuth } from '../../context/AuthContext';

export const PaymentDetailsScreen: React.FC = () => {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { paymentId } = route.params;
  const { isPaymentVerifier, serverUrl } = useAuth();

  const [payment, setPayment] = useState<Payment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Fullscreen image modal
  const [imageModalVisible, setImageModalVisible] = useState(false);

  // Reject modal
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [rejectError, setRejectError] = useState('');

  const fetchPayment = useCallback(async () => {
    try {
      const data = await api.payments.getById(paymentId);
      setPayment(data);
    } catch (e) {
      console.error('Failed to load payment detail', e);
      Alert.alert('Error', 'Unable to load payment information.');
    } finally {
      setIsLoading(false);
    }
  }, [paymentId]);

  useEffect(() => {
    fetchPayment();
  }, [fetchPayment]);

  const handleApprove = () => {
    Alert.alert(
      'Confirm Payment Approval',
      `Have you cross-checked the bank statement for reference "${payment?.reference_number}" and amount of ${Number(payment?.amount).toLocaleString()} ETB? This will finalize the tickets as SOLD.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Approve & Confirm',
          style: 'default',
          onPress: async () => {
            setActionLoading(true);
            try {
              const updated = await api.payments.approve(paymentId);
              setPayment(updated);
              Alert.alert('Success', 'Payment approved successfully! Tickets are now marked SOLD.');
            } catch (err: any) {
              const msg =
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Failed to approve payment.';
              Alert.alert('Approval Error', msg);
            } finally {
              setActionLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      setRejectError('Please specify a rejection reason.');
      return;
    }

    setActionLoading(true);
    try {
      const updated = await api.payments.reject(paymentId, rejectReason.trim());
      setPayment(updated);
      setRejectModalVisible(false);
      setRejectReason('');
      Alert.alert(
        'Payment Rejected',
        'The customer payment has been rejected and the reserved tickets have been released.'
      );
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to reject payment.';
      Alert.alert('Rejection Error', msg);
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading || !payment) {
    return <LoadingScreen message="Loading transaction details..." />;
  }

  // Determine full receipt URL
  let receiptUri = payment.receipt_image || payment.receipt_url;
  if (receiptUri && !receiptUri.startsWith('http')) {
    receiptUri = `${serverUrl}${receiptUri.startsWith('/') ? '' : '/'}${receiptUri}`;
  }

  const isPending = payment.status === 'pending';

  return (
    <View style={styles.container}>
      <Header
        title="Payment Review"
        subtitle={`Ref: ${payment.reference_number}`}
        onBack={() => navigation.goBack()}
      />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Verification Alert Callout */}
        <View style={styles.noticeBox}>
          <ShieldAlert size={20} color={colors.warning} style={styles.noticeIcon} />
          <View style={styles.noticeTextWrapper}>
            <Text style={styles.noticeTitle}>Manual Verification Required</Text>
            <Text style={styles.noticeDesc}>
              Do not approve without verifying that reference code and exact amount appear in your
              official Telebirr or bank statement.
            </Text>
          </View>
        </View>

        {/* Transaction Summary Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardHeaderTitle}>TRANSACTION DETAILS</Text>
            <Badge label={payment.status} variant={payment.status as any} size="md" />
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Reference Code:</Text>
            <Text style={styles.refValue}>{payment.reference_number}</Text>
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Payment Method:</Text>
            <Badge label={payment.payment_method} variant={payment.payment_method as any} />
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Amount Paid:</Text>
            <Text style={styles.amountValue}>{Number(payment.amount).toLocaleString()} ETB</Text>
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Submitted At:</Text>
            <View style={styles.inlineRow}>
              <Calendar size={14} color={colors.textMuted} />
              <Text style={styles.value}>
                {new Date(payment.submitted_at || payment.created_at).toLocaleString()}
              </Text>
            </View>
          </View>

          {payment.status === 'rejected' && payment.rejection_reason && (
            <View style={styles.rejectionBox}>
              <Text style={styles.rejectionTitle}>Rejection Reason:</Text>
              <Text style={styles.rejectionText}>{payment.rejection_reason}</Text>
            </View>
          )}

          {payment.status === 'approved' && payment.verified_by && (
            <View style={styles.approvedBox}>
              <Text style={styles.approvedText}>
                Verified by staff: {payment.verified_by}
              </Text>
            </View>
          )}
        </View>

        {/* Customer Information Card */}
        <View style={styles.card}>
          <Text style={styles.cardHeaderTitle}>CUSTOMER INFORMATION</Text>

          <View style={styles.row}>
            <Text style={styles.label}>Phone Number:</Text>
            <View style={styles.inlineRow}>
              <Phone size={14} color={colors.primaryLight} />
              <Text style={styles.value}>{payment.customer_phone}</Text>
            </View>
          </View>

          {payment.customer_name && (
            <View style={styles.row}>
              <Text style={styles.label}>Customer Name:</Text>
              <Text style={styles.value}>{payment.customer_name}</Text>
            </View>
          )}

          {payment.telegram_username && (
            <View style={styles.row}>
              <Text style={styles.label}>Telegram:</Text>
              <Text style={styles.value}>@{payment.telegram_username}</Text>
            </View>
          )}
        </View>

        {/* Tickets Attached */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardHeaderTitle}>ASSOCIATED TICKETS</Text>
            <Text style={styles.ticketCountBadge}>
              {payment.ticket_numbers?.length || 0} Tickets
            </Text>
          </View>

          {payment.lottery_title && (
            <Text style={styles.lotteryTitle}>Lottery: {payment.lottery_title}</Text>
          )}

          <View style={styles.ticketPillsContainer}>
            {payment.ticket_numbers && payment.ticket_numbers.length > 0 ? (
              payment.ticket_numbers.map((tNum) => (
                <View key={tNum} style={styles.ticketPill}>
                  <Ticket size={14} color={colors.primaryLight} />
                  <Text style={styles.ticketPillText}>#{tNum}</Text>
                </View>
              ))
            ) : (
              <Text style={styles.noTicketsText}>No ticket numbers linked</Text>
            )}
          </View>
        </View>

        {/* Receipt Screenshot Section */}
        <View style={styles.card}>
          <Text style={styles.cardHeaderTitle}>RECEIPT SCREENSHOT</Text>

          {receiptUri ? (
            <TouchableOpacity
              activeOpacity={0.9}
              style={styles.imagePreviewContainer}
              onPress={() => setImageModalVisible(true)}
            >
              <Image
                source={{ uri: receiptUri }}
                style={styles.receiptImage}
                resizeMode="contain"
              />
              <View style={styles.expandOverlay}>
                <Maximize2 size={16} color="#FFFFFF" />
                <Text style={styles.expandText}>Tap to inspect full receipt</Text>
              </View>
            </TouchableOpacity>
          ) : (
            <View style={styles.noReceiptBox}>
              <Text style={styles.noReceiptText}>
                No receipt photo uploaded. Customer submitted transaction reference number only.
              </Text>
            </View>
          )}
        </View>

        {/* Staff Verification Action Buttons */}
        {isPending && isPaymentVerifier && (
          <View style={styles.actionButtonGroup}>
            <Button
              title="Approve Payment"
              variant="success"
              size="lg"
              onPress={handleApprove}
              loading={actionLoading}
              icon={<CheckCircle size={20} color="#FFFFFF" />}
              style={styles.actionButton}
            />

            <Button
              title="Reject Payment"
              variant="danger"
              size="lg"
              onPress={() => {
                setRejectError('');
                setRejectModalVisible(true);
              }}
              disabled={actionLoading}
              icon={<XCircle size={20} color="#FFFFFF" />}
              style={styles.actionButton}
            />
          </View>
        )}
      </ScrollView>

      {/* Fullscreen Image Modal */}
      <Modal
        visible={imageModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setImageModalVisible(false)}
      >
        <View style={styles.imageModalBackdrop}>
          <TouchableOpacity
            style={styles.modalCloseBtn}
            onPress={() => setImageModalVisible(false)}
          >
            <X size={26} color="#FFFFFF" />
          </TouchableOpacity>

          {receiptUri && (
            <Image
              source={{ uri: receiptUri }}
              style={styles.fullscreenImage}
              resizeMode="contain"
            />
          )}
        </View>
      </Modal>

      {/* Rejection Reason Modal */}
      <Modal
        visible={rejectModalVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setRejectModalVisible(false)}
      >
        <View style={styles.rejectModalBackdrop}>
          <View style={styles.rejectModalCard}>
            <Text style={styles.rejectModalTitle}>Reject Payment</Text>
            <Text style={styles.rejectModalSubtitle}>
              Please provide a clear reason for rejecting this transaction. The customer will be
              notified and reserved tickets will be made available again.
            </Text>

            <Input
              label="Rejection Reason"
              value={rejectReason}
              onChangeText={(text) => {
                setRejectReason(text);
                setRejectError('');
              }}
              placeholder="e.g. Reference code not found on bank statement"
              error={rejectError}
              multiline
              numberOfLines={3}
            />

            <View style={styles.presetReasons}>
              {[
                'Transaction reference not found on bank statement',
                'Amount does not match required total',
                'Duplicate reference number used previously',
              ].map((reason) => (
                <TouchableOpacity
                  key={reason}
                  style={styles.presetChip}
                  onPress={() => {
                    setRejectReason(reason);
                    setRejectError('');
                  }}
                >
                  <Text style={styles.presetChipText}>{reason}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.rejectModalActions}>
              <Button
                title="Cancel"
                variant="secondary"
                size="md"
                onPress={() => setRejectModalVisible(false)}
                style={styles.modalActionBtn}
              />
              <Button
                title="Confirm Rejection"
                variant="danger"
                size="md"
                onPress={handleReject}
                loading={actionLoading}
                style={styles.modalActionBtn}
              />
            </View>
          </View>
        </View>
      </Modal>
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
  noticeBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: colors.warning,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  noticeIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  noticeTextWrapper: {
    flex: 1,
  },
  noticeTitle: {
    color: colors.warning,
    fontSize: typography.sm,
    fontWeight: '700',
  },
  noticeDesc: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
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
    marginBottom: spacing.md,
    paddingBottom: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  cardHeaderTitle: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs + 2,
  },
  inlineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  label: {
    color: colors.textSecondary,
    fontSize: typography.sm,
  },
  value: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '500',
  },
  refValue: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  amountValue: {
    color: colors.success,
    fontSize: typography.base,
    fontWeight: '700',
  },
  rejectionBox: {
    backgroundColor: colors.dangerLight,
    borderColor: colors.danger,
    borderWidth: 1,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  rejectionTitle: {
    color: colors.danger,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  rejectionText: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    marginTop: 2,
  },
  approvedBox: {
    backgroundColor: colors.successLight,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  approvedText: {
    color: colors.success,
    fontSize: typography.xs,
    fontWeight: '600',
  },
  ticketCountBadge: {
    color: colors.primaryLight,
    fontSize: typography.xs,
    fontWeight: '600',
  },
  lotteryTitle: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginBottom: spacing.sm,
  },
  ticketPillsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  ticketPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.surfaceLight,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.sm,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  ticketPillText: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  noTicketsText: {
    color: colors.textMuted,
    fontSize: typography.xs,
  },
  imagePreviewContainer: {
    backgroundColor: '#000000',
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    marginTop: spacing.xs,
    position: 'relative',
    height: 220,
  },
  receiptImage: {
    width: '100%',
    height: '100%',
  },
  expandOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xs + 2,
    gap: spacing.xs,
  },
  expandText: {
    color: '#FFFFFF',
    fontSize: typography.xs,
    fontWeight: '600',
  },
  noReceiptBox: {
    backgroundColor: colors.surfaceLight,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: spacing.xs,
    alignItems: 'center',
  },
  noReceiptText: {
    color: colors.textMuted,
    fontSize: typography.xs,
    textAlign: 'center',
  },
  actionButtonGroup: {
    marginTop: spacing.md,
    gap: spacing.sm,
  },
  actionButton: {
    width: '100%',
  },
  imageModalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalCloseBtn: {
    position: 'absolute',
    top: 50,
    right: 20,
    zIndex: 10,
    padding: spacing.sm,
  },
  fullscreenImage: {
    width: '90%',
    height: '80%',
  },
  rejectModalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  rejectModalCard: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    padding: spacing.xl,
    borderColor: colors.border,
    borderWidth: 1,
  },
  rejectModalTitle: {
    color: colors.danger,
    fontSize: typography.lg,
    fontWeight: '700',
  },
  rejectModalSubtitle: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 4,
    marginBottom: spacing.md,
  },
  presetReasons: {
    gap: spacing.xs,
    marginBottom: spacing.lg,
  },
  presetChip: {
    backgroundColor: colors.surfaceLight,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.sm,
    padding: spacing.sm,
  },
  presetChipText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  rejectModalActions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  modalActionBtn: {
    flex: 1,
  },
});
