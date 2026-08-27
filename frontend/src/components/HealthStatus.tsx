import { useEffect, useState } from "react";

type HealthStatus = {
  status: string;
  service: string;
  version: string;
  timestamp: string;
};

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Health check failed");
        }
        return response.json();
      })
      .then((data) => setHealth(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div>Checking system status...</div>;
  }

  if (error || !health) {
    return <div>System status unavailable</div>;
  }

  return (
    <div>
      <strong>System Status: {health.status}</strong>
      <div>API Version: {health.version}</div>
      <div>
        Last checked: {new Date(health.timestamp).toLocaleString()}
      </div>
    </div>
  );
}