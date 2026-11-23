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
import {
  Bell,
  CheckCircle,
  CreditCard,
  Trophy,
  Clock,
  CheckCheck,
} from 'lucide-react-native';
import { colors, borderRadius, typography, spacing } from '../../theme/colors';
import { Header } from '../../components/Header';
import { EmptyState } from '../../components/EmptyState';
import { LoadingScreen } from '../../components/LoadingScreen';
import { api } from '../../api/endpoints';
import { NotificationItem } from '../../types/api';

export const NotificationsScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.notifications.list();
      setNotifications(data);
    } catch (e) {
      console.error('Failed to load notifications', e);
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    setIsLoading(true);
    fetchNotifications();
  }, [fetchNotifications]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchNotifications();
  };

  const handleMarkAllRead = async () => {
    try {
      await api.notifications.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (e) {
      console.error('Failed to mark all as read', e);
    }
  };

  const handleItemPress = async (item: NotificationItem) => {
    if (!item.is_read) {
      try {
        await api.notifications.markRead(item.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n))
        );
      } catch (e) {
        console.error('Failed to mark item read', e);
      }
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'payment':
        return <CreditCard size={18} color={colors.warning} />;
      case 'draw':
        return <Trophy size={18} color={colors.gold} />;
      case 'reservation':
        return <Clock size={18} color={colors.info} />;
      case 'system':
      default:
        return <Bell size={18} color={colors.primaryLight} />;
    }
  };

  const renderNotification = ({ item }: { item: NotificationItem }) => {
    return (
      <TouchableOpacity
        activeOpacity={0.8}
        style={[styles.itemCard, !item.is_read ? styles.unreadCard : null]}
        onPress={() => handleItemPress(item)}
      >
        <View style={styles.iconContainer}>{getIcon(item.notification_type)}</View>

        <View style={styles.contentContainer}>
          <View style={styles.topRow}>
            <Text style={styles.title} numberOfLines={1}>
              {item.title}
            </Text>
            {!item.is_read && <View style={styles.unreadDot} />}
          </View>

          <Text style={styles.message}>{item.message}</Text>
          <Text style={styles.timeText}>
            {new Date(item.created_at).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Header
        title="Notifications"
        subtitle="Operational Alerts"
        onBack={() => navigation.goBack()}
        rightAction={
          <TouchableOpacity
            onPress={handleMarkAllRead}
            style={styles.markAllBtn}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <CheckCheck size={18} color={colors.primaryLight} />
          </TouchableOpacity>
        }
      />

      {isLoading ? (
        <LoadingScreen message="Loading notifications..." />
      ) : (
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          renderItem={renderNotification}
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
              title="No notifications"
              message="You have no unread operational alerts or messages."
              icon={<Bell size={36} color={colors.textMuted} />}
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
  markAllBtn: {
    padding: spacing.xs,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    gap: spacing.md,
  },
  unreadCard: {
    borderColor: colors.primary,
    backgroundColor: 'rgba(99, 102, 241, 0.05)',
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contentContainer: {
    flex: 1,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  title: {
    color: colors.textPrimary,
    fontSize: typography.sm,
    fontWeight: '700',
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.primary,
    marginLeft: spacing.xs,
  },
  message: {
    color: colors.textSecondary,
    fontSize: typography.xs,
    lineHeight: 18,
  },
  timeText: {
    color: colors.textMuted,
    fontSize: typography.xs - 2,
    marginTop: 4,
  },
});
