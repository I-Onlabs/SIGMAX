import { useState } from 'react';
import AppShell, { type TabId } from './ui/layout/AppShell';
import OverviewScreen from './screens/OverviewScreen';
import AnalysisScreen from './screens/AnalysisScreen';
import EventsScreen from './screens/EventsScreen';
import HealthScreen from './screens/HealthScreen';
import ConnectionsScreen from './screens/ConnectionsScreen';
import { useWebSocket } from './hooks/useWebSocket';
import api from './services/api';
import { getConnectionLabel, resolveConnectionState } from './ui/state';

export default function App() {
  const {
    connected,
    systemStatus,
    marketData,
    portfolio,
    systemHealth,
    tradeExecutions,
    agentDecisions,
  } = useWebSocket();

  const [controlLoading, setControlLoading] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  const connectionLabel = getConnectionLabel(resolveConnectionState(connected));
  const themeLabel = theme === 'dark' ? 'Light Mode' : 'Dark Mode';

  const handleToggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleStartTrading = async () => {
    setControlLoading('start');
    try {
      await api.startTrading();
    } catch (error) {
      console.error('Failed to start trading:', error);
      alert('Failed to start trading: ' + (error as Error).message);
    } finally {
      setControlLoading(null);
    }
  };

  const handlePauseTrading = async () => {
    setControlLoading('pause');
    try {
      await api.pauseTrading();
    } catch (error) {
      console.error('Failed to pause trading:', error);
      alert('Failed to pause trading: ' + (error as Error).message);
    } finally {
      setControlLoading(null);
    }
  };

  const handleEmergencyStop = async () => {
    if (!confirm('Emergency Stop will close all positions immediately. Continue?')) {
      return;
    }

    setControlLoading('stop');
    try {
      const result = await api.emergencyStop();
      alert(`Emergency stop executed. Positions closed: ${result.positions_closed || 0}`);
    } catch (error) {
      console.error('Emergency stop failed:', error);
      alert('Emergency stop failed: ' + (error as Error).message);
    } finally {
      setControlLoading(null);
    }
  };

  return (
    <div data-theme={theme}>
      <AppShell
        title="Dashboard"
        activeTab={activeTab}
        onTabChange={setActiveTab}
        connectionLabel={connectionLabel}
        themeLabel={themeLabel}
        onToggleTheme={handleToggleTheme}
      >
        {activeTab === 'overview' && (
          <OverviewScreen
            systemStatus={systemStatus}
            portfolio={portfolio}
            agentDecisions={agentDecisions}
            tradeExecutions={tradeExecutions}
            controlLoading={controlLoading}
            onStartTrading={handleStartTrading}
            onPauseTrading={handlePauseTrading}
            onEmergencyStop={handleEmergencyStop}
          />
        )}

        {activeTab === 'analysis' && (
          <AnalysisScreen marketData={marketData} agentDecisions={agentDecisions} />
        )}

        {activeTab === 'events' && (
          <EventsScreen tradeExecutions={tradeExecutions} />
        )}

        {activeTab === 'health' && (
          <HealthScreen
            systemStatus={systemStatus}
            systemHealth={systemHealth}
            portfolio={portfolio}
          />
        )}

        {activeTab === 'connections' && <ConnectionsScreen />}
      </AppShell>
    </div>
  );
}
