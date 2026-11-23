import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Modal,
} from 'react-native';
import { ShieldCheck, Server, Eye, EyeOff, Lock, Mail } from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { useAuth } from '../../context/AuthContext';

export const LoginScreen: React.FC = () => {
  const { login, serverUrl, updateServerUrl } = useAuth();

  const [email, setEmail] = useState('verifier@lottery.com');
  const [password, setPassword] = useState('verifier123');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Server host modal
  const [showServerModal, setShowServerModal] = useState(false);
  const [customServerUrl, setCustomServerUrl] = useState(serverUrl);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setErrorMessage('');
    setIsLoading(true);

    try {
      await login(email.trim(), password.trim());
    } catch (err: any) {
      console.error('Login failed', err);
      const detail =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Authentication failed. Please check your credentials or server connection.';
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillDemo = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMessage('');
  };

  const handleSaveServerUrl = async () => {
    try {
      await updateServerUrl(customServerUrl.trim());
      setShowServerModal(false);
      Alert.alert('Success', 'Server URL updated successfully.');
    } catch (e) {
      Alert.alert('Error', 'Failed to update server URL.');
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Brand Header */}
        <View style={styles.brandHeader}>
          <View style={styles.iconCircle}>
            <ShieldCheck size={40} color={colors.primaryLight} />
          </View>
          <Text style={styles.appTitle}>LOTTERY ADMIN</Text>
          <Text style={styles.appSubtitle}>Authorized Staff Mobile Portal</Text>
        </View>

        {/* Login Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Staff Sign In</Text>
          <Text style={styles.cardSubtitle}>Enter your credentials to access operations</Text>

          {errorMessage ? (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>{errorMessage}</Text>
            </View>
          ) : null}

          <Input
            label="Staff Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="staff@lottery.com"
            leftIcon={<Mail size={18} color={colors.textMuted} />}
          />

          <Input
            label="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            placeholder="••••••••"
            leftIcon={<Lock size={18} color={colors.textMuted} />}
            rightIcon={
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                {showPassword ? (
                  <EyeOff size={18} color={colors.textMuted} />
                ) : (
                  <Eye size={18} color={colors.textMuted} />
                )}
              </TouchableOpacity>
            }
          />

          <Button
            title="Sign In to Dashboard"
            onPress={handleLogin}
            loading={isLoading}
            style={styles.loginBtn}
          />

          {/* Demo Logins */}
          <View style={styles.demoSection}>
            <Text style={styles.demoLabel}>QUICK DEMO ACCESS</Text>
            <View style={styles.demoGrid}>
              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleFillDemo('verifier@lottery.com', 'verifier123')}
              >
                <Text style={styles.demoRole}>Payment Verifier</Text>
                <Text style={styles.demoEmail}>verifier@lottery.com</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleFillDemo('admin@lottery.com', 'admin123')}
              >
                <Text style={styles.demoRole}>Super Admin</Text>
                <Text style={styles.demoEmail}>admin@lottery.com</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Server Host Config Button */}
        <TouchableOpacity
          style={styles.serverConfigBtn}
          onPress={() => {
            setCustomServerUrl(serverUrl);
            setShowServerModal(true);
          }}
        >
          <Server size={14} color={colors.textMuted} />
          <Text style={styles.serverConfigText} numberOfLines={1}>
            API Host: {serverUrl}
          </Text>
        </TouchableOpacity>
      </ScrollView>

      {/* Server Config Modal */}
      <Modal
        visible={showServerModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowServerModal(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Backend API Host</Text>
            <Text style={styles.modalSubtitle}>
              Configure the Django REST API host for local emulators or staging servers.
            </Text>

            <Input
              label="API Base URL"
              value={customServerUrl}
              onChangeText={setCustomServerUrl}
              placeholder="http://10.0.2.2:8000"
              autoCapitalize="none"
            />

            <View style={styles.presetRow}>
              <TouchableOpacity
                style={styles.presetChip}
                onPress={() => setCustomServerUrl('http://localhost:8000')}
              >
                <Text style={styles.presetChipText}>Web/iOS (localhost)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.presetChip}
                onPress={() => setCustomServerUrl('http://10.0.2.2:8000')}
              >
                <Text style={styles.presetChipText}>Android (10.0.2.2)</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.modalActions}>
              <Button
                title="Cancel"
                variant="secondary"
                size="sm"
                onPress={() => setShowServerModal(false)}
                style={styles.modalActionBtn}
              />
              <Button
                title="Save Host"
                size="sm"
                onPress={handleSaveServerUrl}
                style={styles.modalActionBtn}
              />
            </View>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: spacing.xl,
  },
  brandHeader: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  iconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  appTitle: {
    color: colors.textPrimary,
    fontSize: typography.xl,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  appSubtitle: {
    color: colors.textSecondary,
    fontSize: typography.sm,
    marginTop: 2,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 5,
  },
  cardTitle: {
    color: colors.textPrimary,
    fontSize: typography.lg,
    fontWeight: '700',
  },
  cardSubtitle: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    marginTop: 2,
    marginBottom: spacing.lg,
  },
  errorBanner: {
    backgroundColor: colors.dangerLight,
    borderColor: colors.danger,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorBannerText: {
    color: colors.danger,
    fontSize: typography.xs,
    fontWeight: '500',
  },
  loginBtn: {
    marginTop: spacing.sm,
  },
  demoSection: {
    marginTop: spacing.xl,
    paddingTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  demoLabel: {
    color: colors.textMuted,
    fontSize: typography.xs,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  demoGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  demoChip: {
    flex: 1,
    backgroundColor: colors.surfaceLight,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
  },
  demoRole: {
    color: colors.primaryLight,
    fontSize: typography.xs,
    fontWeight: '700',
  },
  demoEmail: {
    color: colors.textMuted,
    fontSize: typography.xs - 1,
    marginTop: 2,
  },
  serverConfigBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.xl,
    paddingVertical: spacing.sm,
    gap: spacing.xs,
  },
  serverConfigText: {
    color: colors.textMuted,
    fontSize: typography.xs,
    maxWidth: 240,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
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
