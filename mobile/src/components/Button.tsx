import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { colors, borderRadius, typography, spacing } from '../theme/colors';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  style,
  textStyle,
  icon,
}) => {
  const getButtonStyles = () => {
    switch (variant) {
      case 'danger':
        return { bg: colors.danger, text: '#FFFFFF', border: 'transparent' };
      case 'success':
        return { bg: colors.success, text: '#FFFFFF', border: 'transparent' };
      case 'secondary':
        return { bg: colors.surfaceLight, text: colors.textPrimary, border: colors.border };
      case 'outline':
        return { bg: 'transparent', text: colors.primaryLight, border: colors.primary };
      case 'primary':
      default:
        return { bg: colors.primary, text: '#FFFFFF', border: 'transparent' };
    }
  };

  const scheme = getButtonStyles();

  const getPadding = () => {
    switch (size) {
      case 'sm':
        return { py: spacing.xs + 2, px: spacing.md, font: typography.xs };
      case 'lg':
        return { py: spacing.lg, px: spacing.xxl, font: typography.base };
      case 'md':
      default:
        return { py: spacing.md, px: spacing.lg, font: typography.sm };
    }
  };

  const pad = getPadding();

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      disabled={disabled || loading}
      style={[
        styles.button,
        {
          backgroundColor: scheme.bg,
          borderColor: scheme.border,
          paddingVertical: pad.py,
          paddingHorizontal: pad.px,
          opacity: disabled ? 0.5 : 1,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={scheme.text} size="small" />
      ) : (
        <>
          {icon ? <>{icon}</> : null}
          <Text
            style={[
              styles.text,
              {
                color: scheme.text,
                fontSize: pad.font,
                marginLeft: icon ? spacing.xs : 0,
              },
              textStyle,
            ]}
          >
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: borderRadius.md,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    fontWeight: '600',
  },
});
