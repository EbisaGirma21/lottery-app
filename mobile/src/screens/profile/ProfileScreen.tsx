import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Modal,
} from 'react-native';
import {
  User,
  Shield,
  Server,
  LogOut,
  CheckCircle,
  Key,
  Info,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { useAuth } from '../../context/AuthContext';

export const ProfileScreen: React.FC = () => {
  const { user, logout, isPaymentVerifier, isDrawOfficer, isSuperAdmin, serverUrl, updateServerUrl } =
    useAuth();

  const [showServerModal, setShowServerModal] = useState(false);
  const [newServerUrl, setNewServerUrl] = useState(serverUrl);

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to log out of your staff session?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Sign Out',
        style: 'destructive',
        onPress: () => logout(),
      },
    ]);
  };

  const handleSaveHost = async () => {
    try {
      await updateServerUrl(newServerUrl.trim());
      setShowServerModal(false);
      Alert.alert('Success', 'Backend API server URL updated.');
    } catch (e) {
      Alert.alert('Error', 'Failed to update backend URL.');
    }
  };

  const initials = `${(user?.first_name?.[0] || user?.email?.[0] || 'S').toUpperCase()}`;

  return (
    <View style={styles.container}>
      <Header title="Staff Profile" subtitle="Account & Configuration" />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>

          <Text style={styles.userName}>
            {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : 'Staff Member'}
          </Text>
          <Text style={styles.userEmail}>{user?.email}</Text>

          <View style={styles.roleBadgeContainer}>
            <Badge
              label={user?.role?.replace('_', ' ') || 'STAFF'}
              variant="primary"
              size="md"
            />
          </View>
        </View>

        {/* Permissions Overview */}
        <View style={styles.card}>
          <Text style={styles.cardHeading}>ACTIVE PERMISSIONS</Text>

          <View style={styles.permRow}>
            <View style={styles.permLeft}>
              <CheckCircle
                size={16}
                color={isPaymentVerifier ? colors.success : colors.textMuted}
              />
              <Text style={styles.permText}>Manual Payment Verification</Text>
            </View>
            <Text
              style={[
                styles.permStatus,
                { color: isPaymentVerifier ? colors.success : colors.textMuted },
              ]}
            >
              {isPaymentVerifier ? 'GRANTED' : 'RESTRICTED'}
            </Text>
          </View>

          <View style={styles.permRow}>
            <View style={styles.permLeft}>
              <CheckCircle
                size={16}
                color={isDrawOfficer ? colors.success : colors.textMuted}
              />
              <Text style={styles.permText}>Cryptographic Draw Execution</Text>
            </View>
            <Text
              style={[
                styles.permStatus,
                { color: isDrawOfficer ? colors.success : colors.textMuted },
              ]}
            >
              {isDrawOfficer ? 'GRANTED' : 'RESTRICTED'}
            </Text>
          </View>

          <View style={styles.permRow}>
            <View style={styles.permLeft}>
              <CheckCircle
                size={16}
                color={isSuperAdmin ? colors.success : colors.textMuted}
              />
              <Text style={styles.permText}>Lottery Management & Capacity Setup</Text>
            </View>
            <Text
              style={[
                styles.permStatus,
                { color: isSuperAdmin ? colors.success : colors.textMuted },
              ]}
            >
              {isSuperAdmin ? 'GRANTED' : 'RESTRICTED'}
            </Text>
          </View>
        </View>

        {/* Server & Environment Configuration */}
        <View style={styles.card}>
          <Text style={styles.cardHeading}>API SERVER CONNECTION</Text>

          <View style={styles.serverInfoRow}>
            <Server size={18} color={colors.primaryLight} />
            <View style={styles.serverDetails}>
              <Text style={styles.serverLabel}>Backend Host URL</Text>
              <Text style={styles.serverUrlText} numberOfLines={1}>
                {serverUrl}
              </Text>
            </View>
          </View>

          <Button
            title="Change API Host URL"
            variant="outline"
            size="sm"
            onPress={() => {
              setNewServerUrl(serverUrl);
              setShowServerModal(true);
            }}
            style={styles.changeHostBtn}
          />
        </View>

        {/* Security & System Info */}
        <View style={styles.card}>
          <Text style={styles.cardHeading}>SYSTEM & SECURITY</Text>

          <View style={styles.row}>
            <Text style={styles.label}>Authentication Method:</Text>
            <Text style={styles.value}>JWT Bearer Token</Text>
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Draw Randomness:</Text>
            <Text style={styles.value}>Python secrets + SHA-256</Text>
          </View>

          <View style={styles.row}>
            <Text style={styles.label}>Mobile App Version:</Text>
            <Text style={styles.value}>1.0.0 (Production)</Text>
          </View>
        </View>

        {/* Logout Button */}
        <Button
          title="Sign Out of Portal"
          variant="danger"
          size="lg"
          onPress={handleLogout}
          icon={<LogOut size={20} color="#FFFFFF" />}
          style={styles.logoutBtn}
        />
      </ScrollView>

      {/* Host URL Modal */}
      <Modal
        visible={showServerModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowServerModal(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Update Backend Host</Text>
            <Text style={styles.modalSubtitle}>
              Configure the Django REST API URL for testing or production.
            </Text>

            <Input
              label="Backend URL"
              value={newServerUrl}
              onChangeText={setNewServerUrl}
              autoCapitalize="none"
              placeholder="http://10.0.2.2:8000"
            />

            <View style={styles.presetRow}>
              <TouchableOpacity
                style={styles.presetChip}
                onPress={() => setNewServerUrl('http://localhost:8000')}
              >
                <Text style={styles.presetChipText}>Localhost</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.presetChip}
                onPress={() => setNewServerUrl('http://10.0.2.2:8000')}
              >
                <Text style={styles.presetChipText}>Android (10.0.2.2)</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalActions}>
              <Button
                title="Cancel"
                variant="secondary"
                size="md"
                onPress={() => setShowServerModal(false)}
                style={styles.modalActionBtn}
              />
              <Button
                title="Save & Connect"
                size="md"
                onPress={handleSaveHost}
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
  userCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  avatarCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  avatarText: {
    color: '#FFFFFF',
    fontSize: typography.xl,
    fontWeight: '800',
  },
  userName: {
    color: colors.textPrimary,
    fontSize: typography.lg,
    fontWeight: '700',
  },
  userEmail: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
    marginBottom: spacing.md,
  },
  roleBadgeContainer: {
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
  cardHeading: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: spacing.md,
  },
  permRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs + 2,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.05)',
  },
  permLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  permText: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    fontWeight: '500',
  },
  permStatus: {
    fontSize: typography.xs - 2,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  serverInfoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surfaceLight,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  serverDetails: {
    flex: 1,
  },
  serverLabel: {
    color: colors.textMuted,
    fontSize: typography.xs - 2,
    textTransform: 'uppercase',
  },
  serverUrlText: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    fontFamily: 'monospace',
    marginTop: 2,
  },
  changeHostBtn: {
    marginTop: spacing.sm,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.xs,
  },
  label: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  value: {
    color: colors.textPrimary,
    fontSize: typography.xs,
    fontWeight: '600',
  },
  logoutBtn: {
    marginTop: spacing.md,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  modalCard: {
    width: '100%',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
  },
  modalTitle: {
    color: colors.textPrimary,
    fontSize: typography.md,
    fontWeight: '700',
  },
  modalSubtitle: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 4,
    marginBottom: spacing.md,
  },
  presetRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  presetChip: {
    flex: 1,
    paddingVertical: spacing.xs + 2,
    paddingHorizontal: spacing.sm,
    borderRadius: borderRadius.sm,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  presetChipText: {
    color: colors.textSecondary,
    fontSize: typography.xs,
  },
  modalActions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  modalActionBtn: {
    flex: 1,
  },
});
