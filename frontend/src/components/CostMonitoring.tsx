import React, { useState, useEffect } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot, query, orderBy, limit, where } from 'firebase/firestore';
import ErrorBoundary from './ErrorBoundary';

type CostRecord = {
  id: string;
  job_id: string;
  service: string;
  cost_usd: number;
  timestamp: any;
  details: any;
};

type CostSummary = {
  total: number;
  bfl_api: number;
  google_storage: number;
  count: number;
  period: string;
};

const CostMonitoring = () => {
  const [costs, setCosts] = useState<CostRecord[]>([]);
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'7' | '30' | '90'>('30');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCosts = () => {
      try {
        const costsCollection = collection(db, 'costs');
        const q = query(
          costsCollection,
          orderBy('timestamp', 'desc'),
          limit(100)
        );

        const unsubscribe = onSnapshot(q, (snapshot) => {
          const costsFromFirestore: CostRecord[] = [];
          snapshot.forEach(doc => {
            const data = doc.data();
            costsFromFirestore.push({ 
              id: doc.id, 
              ...data,
              timestamp: data.timestamp?.toDate?.() || new Date()
            } as CostRecord);
          });
          
          setCosts(costsFromFirestore);
          calculateSummary(costsFromFirestore, parseInt(selectedPeriod));
          setIsLoading(false);
          setError(null);
        }, (error) => {
          console.error('Error loading costs:', error);
          setError('Failed to load cost data');
          setIsLoading(false);
        });

        return unsubscribe;
      } catch (error: any) {
        console.error('Error setting up cost listener:', error);
        setError(`Setup error: ${error.message}`);
        setIsLoading(false);
        return () => {};
      }
    };

    const unsubscribe = loadCosts();
    return () => unsubscribe();
  }, [selectedPeriod]);

  const calculateSummary = (allCosts: CostRecord[], days: number) => {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    const recentCosts = allCosts.filter(cost => 
      cost.timestamp && new Date(cost.timestamp) > cutoffDate
    );

    let bflTotal = 0;
    let storageTotal = 0;

    recentCosts.forEach(cost => {
      if (cost.service === 'bfl_api') {
        bflTotal += cost.cost_usd;
      } else if (cost.service === 'google_storage') {
        storageTotal += cost.cost_usd;
      }
    });

    setSummary({
      total: bflTotal + storageTotal,
      bfl_api: bflTotal,
      google_storage: storageTotal,
      count: recentCosts.length,
      period: `${days} days`
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(amount);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const getServiceIcon = (service: string) => {
    switch (service) {
      case 'bfl_api': return '🎨';
      case 'google_storage': return '☁️';
      default: return '💰';
    }
  };

  const getServiceName = (service: string) => {
    switch (service) {
      case 'bfl_api': return 'BFL API';
      case 'google_storage': return 'Google Storage';
      default: return service;
    }
  };


  const theme = {
    colors: {
      primary: '#5865f2',
      surface: '#23272a',
      text: '#ffffff',
      textMuted: '#99aab5',
      border: '#40444b',
      success: '#57f287',
      warning: '#faa61a',
      error: '#ed4245',
    }
  };

  const styles = {
    container: {
      color: theme.colors.text,
      maxWidth: '100%',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '1.5rem',
    },
    title: {
      margin: 0,
      color: theme.colors.text,
    },
    periodSelector: {
      display: 'flex',
      gap: '0.5rem',
    },
    periodButton: {
      padding: '0.5rem 1rem',
      border: `1px solid ${theme.colors.border}`,
      borderRadius: '6px',
      backgroundColor: theme.colors.surface,
      color: theme.colors.textMuted,
      cursor: 'pointer',
      fontSize: '0.9rem',
    },
    periodButtonActive: {
      backgroundColor: theme.colors.primary,
      color: 'white',
      borderColor: theme.colors.primary,
    },
    summaryGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '1rem',
      marginBottom: '2rem',
    },
    summaryCard: {
      backgroundColor: theme.colors.surface,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: '8px',
      padding: '1.5rem',
      textAlign: 'center' as const,
    },
    summaryValue: {
      fontSize: '1.8rem',
      fontWeight: 'bold',
      margin: '0.5rem 0',
    },
    summaryLabel: {
      color: theme.colors.textMuted,
      fontSize: '0.9rem',
      margin: 0,
    },
    recentCosts: {
      backgroundColor: theme.colors.surface,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: '8px',
      padding: '1.5rem',
    },
    costItem: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.75rem 0',
      borderBottom: `1px solid ${theme.colors.border}`,
    },
    costItemLast: {
      borderBottom: 'none',
    },
    costLeft: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      flex: 1,
    },
    costService: {
      fontWeight: 'bold',
      fontSize: '0.9rem',
    },
    costDetails: {
      color: theme.colors.textMuted,
      fontSize: '0.8rem',
    },
    costAmount: {
      fontWeight: 'bold',
      fontSize: '0.9rem',
    },
    loading: {
      textAlign: 'center' as const,
      padding: '2rem',
      color: theme.colors.textMuted,
    },
    error: {
      backgroundColor: `${theme.colors.error}20`,
      color: theme.colors.error,
      border: `1px solid ${theme.colors.error}40`,
      padding: '1rem',
      borderRadius: '6px',
      marginBottom: '1rem',
    },
  };

  if (isLoading) {
    return (
      <div style={styles.loading}>
        <div>💰 Loading cost data...</div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>💰 Cost Monitoring</h2>
          <div style={styles.periodSelector}>
            {(['7', '30', '90'] as const).map(period => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                style={{
                  ...styles.periodButton,
                  ...(selectedPeriod === period ? styles.periodButtonActive : {})
                }}
              >
                {period} days
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div style={styles.error}>
            ❌ {error}
          </div>
        )}

        {summary && (
          <>
            <div style={styles.summaryGrid}>
              <div style={styles.summaryCard}>
                <div style={{...styles.summaryValue, color: theme.colors.primary}}>
                  {formatCurrency(summary.total)}
                </div>
                <p style={styles.summaryLabel}>Total Cost ({summary.period})</p>
              </div>
              
              <div style={styles.summaryCard}>
                <div style={{...styles.summaryValue, color: theme.colors.success}}>
                  {formatCurrency(summary.bfl_api)}
                </div>
                <p style={styles.summaryLabel}>🎨 BFL API</p>
              </div>
              
              <div style={styles.summaryCard}>
                <div style={{...styles.summaryValue, color: theme.colors.warning}}>
                  {formatCurrency(summary.google_storage)}
                </div>
                <p style={styles.summaryLabel}>☁️ Google Storage</p>
              </div>
              
              <div style={styles.summaryCard}>
                <div style={{...styles.summaryValue, color: theme.colors.textMuted}}>
                  {summary.count}
                </div>
                <p style={styles.summaryLabel}>Total Operations</p>
              </div>
            </div>


            <div style={styles.recentCosts}>
              <h3 style={{marginTop: 0}}>Recent Costs</h3>
              {costs.length === 0 ? (
                <p style={{color: theme.colors.textMuted, textAlign: 'center'}}>
                  No cost data available yet
                </p>
              ) : (
                costs.slice(0, 10).map((cost, index) => (
                  <div 
                    key={cost.id}
                    style={{
                      ...styles.costItem,
                      ...(index === Math.min(costs.length - 1, 9) ? styles.costItemLast : {})
                    }}
                  >
                    <div style={styles.costLeft}>
                      <span>{getServiceIcon(cost.service)}</span>
                      <div>
                        <div style={styles.costService}>
                          {getServiceName(cost.service)}
                        </div>
                        <div style={styles.costDetails}>
                          {formatDate(new Date(cost.timestamp))} • Job: {cost.job_id.slice(0, 8)}...
                          {cost.details?.steps && ` • ${cost.details.steps} steps`}
                        </div>
                      </div>
                    </div>
                    <div style={styles.costAmount}>
                      {formatCurrency(cost.cost_usd)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default CostMonitoring;