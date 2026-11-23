import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, borderRadius, typography } from '../theme/colors';

interface BadgeProps {
  label: string;
  variant?:
    | 'pending'
    | 'approved'
    | 'rejected'
    | 'open'
    | 'closed'
    | 'paused'
    | 'drawn'
    | 'draft'
    | 'available'
    | 'reserved'
    | 'sold'
    | 'primary'
    | 'telebirr'
    | 'cbe'
    | 'cbeBirr'
    | 'awash';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ label, variant = 'primary', size = 'sm' }) => {
  const getColors = () => {
    switch (variant) {
      case 'approved':
      case 'open':
      case 'sold':
        return { bg: colors.successLight, text: colors.success, border: 'rgba(16, 185, 129, 0.3)' };
      case 'pending':
      case 'reserved':
      case 'paused':
        return { bg: colors.warningLight, text: colors.warning, border: 'rgba(245, 158, 11, 0.3)' };
      case 'rejected':
      case 'closed':
        return { bg: colors.dangerLight, text: colors.danger, border: 'rgba(239, 68, 68, 0.3)' };
      case 'drawn':
        return { bg: colors.goldMuted, text: colors.gold, border: 'rgba(251, 191, 36, 0.3)' };
      case 'available':
      case 'draft':
        return { bg: 'rgba(156, 163, 175, 0.15)', text: colors.textSecondary, border: 'rgba(156, 163, 175, 0.3)' };
      case 'telebirr':
        return { bg: 'rgba(0, 114, 206, 0.15)', text: '#38BDF8', border: 'rgba(0, 114, 206, 0.3)' };
      case 'cbe':
        return { bg: 'rgba(128, 0, 32, 0.25)', text: '#F472B6', border: 'rgba(128, 0, 32, 0.4)' };
      case 'cbeBirr':
        return { bg: 'rgba(162, 28, 175, 0.2)', text: '#E879F9', border: 'rgba(162, 28, 175, 0.4)' };
      case 'awash':
        return { bg: 'rgba(30, 58, 138, 0.2)', text: '#60A5FA', border: 'rgba(30, 58, 138, 0.4)' };
      case 'primary':
      default:
        return { bg: colors.primaryMuted, text: colors.primaryLight, border: 'rgba(99, 102, 241, 0.3)' };
    }
  };

  const scheme = getColors();
  const isSm = size === 'sm';

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: scheme.bg,
          borderColor: scheme.border,
          paddingVertical: isSm ? 2 : 4,
          paddingHorizontal: isSm ? 8 : 12,
        },
      ]}
    >
      <Text
        style={[
          styles.text,
          {
            color: scheme.text,
            fontSize: isSm ? typography.xs : typography.sm,
          },
        ]}
      >
        {label.toUpperCase()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    borderRadius: borderRadius.full,
    borderWidth: 1,
    alignSelf: 'flex-start',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontWeight: '700',
    letterSpacing: 0.6,
  },
});
