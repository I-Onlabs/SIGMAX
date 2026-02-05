import StatusPanel from '../components/StatusPanel';
import RiskDashboard from '../components/RiskDashboard';

interface HealthScreenProps {
  systemStatus: any;
  systemHealth: any;
  portfolio: any;
}

export default function HealthScreen({ systemStatus, systemHealth, portfolio }: HealthScreenProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <StatusPanel status={systemStatus} health={systemHealth} />
      <RiskDashboard portfolio={portfolio} status={systemStatus} />
    </div>
  );
}
