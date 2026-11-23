import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  LayoutDashboard,
  CreditCard,
  Ticket,
  Search,
  Trophy,
  User,
} from 'lucide-react-native';
import { colors, typography } from '../theme/colors';
import { MainTabParamList } from '../types/navigation';
import { DashboardScreen } from '../screens/dashboard/DashboardScreen';
import { PendingPaymentsScreen } from '../screens/payments/PendingPaymentsScreen';
import { LotteriesScreen } from '../screens/lotteries/LotteriesScreen';
import { TicketSearchScreen } from '../screens/tickets/TicketSearchScreen';
import { WinnersScreen } from '../screens/winners/WinnersScreen';
import { ProfileScreen } from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

export const AppTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarActiveTintColor: colors.primaryLight,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: {
          fontSize: typography.xs - 2,
          fontWeight: '700',
        },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          tabBarLabel: 'Dashboard',
          tabBarIcon: ({ color, size }) => <LayoutDashboard size={size - 2} color={color} />,
        }}
      />
      <Tab.Screen
        name="Payments"
        component={PendingPaymentsScreen}
        options={{
          tabBarLabel: 'Payments',
          tabBarIcon: ({ color, size }) => <CreditCard size={size - 2} color={color} />,
        }}
      />
      <Tab.Screen
        name="Lotteries"
        component={LotteriesScreen}
        options={{
          tabBarLabel: 'Lotteries',
          tabBarIcon: ({ color, size }) => <Ticket size={size - 2} color={color} />,
        }}
      />
      <Tab.Screen
        name="Tickets"
        component={TicketSearchScreen}
        options={{
          tabBarLabel: 'Search',
          tabBarIcon: ({ color, size }) => <Search size={size - 2} color={color} />,
        }}
      />
      <Tab.Screen
        name="Winners"
        component={WinnersScreen}
        options={{
          tabBarLabel: 'Winners',
          tabBarIcon: ({ color, size }) => <Trophy size={size - 2} color={color} />,
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarLabel: 'Profile',
          tabBarIcon: ({ color, size }) => <User size={size - 2} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
};
