/**
 * Custom hook for fetching reports from the Reports Service API.
 *
 * All requests go through bionicpro-auth proxy which:
 * - Validates the user session
 * - Injects the Bearer token
 * - Ensures user can only access their own reports
 */

import { useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  UserReportsList,
  DailyReport,
  UserSummary,
  ReportsListResponse,
  ReportDetailResponse,
  UserSummaryResponse,
} from '../types/reports';

const AUTH_URL = process.env.REACT_APP_AUTH_URL || 'http://localhost:8000';

interface UseReportsReturn {
  // Data
  reportsList: UserReportsList | null;
  dailyReport: DailyReport | null;
  userSummary: UserSummary | null;

  // State
  loading: boolean;
  error: string | null;

  // Actions
  fetchReportsList: () => Promise<void>;
  fetchDailyReport: (date: string) => Promise<void>;
  fetchUserSummary: () => Promise<void>;
  clearCache: () => Promise<void>;
  clearError: () => void;
}

export const useReports = (): UseReportsReturn => {
  const { authenticated } = useAuth();

  const [reportsList, setReportsList] = useState<UserReportsList | null>(null);
  const [dailyReport, setDailyReport] = useState<DailyReport | null>(null);
  const [userSummary, setUserSummary] = useState<UserSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch with authentication - uses session cookie
   */
  const fetchWithAuth = useCallback(async (url: string): Promise<Response> => {
    return fetch(`${AUTH_URL}${url}`, {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    });
  }, []);

  /**
   * Handle API errors
   */
  const handleError = useCallback((response: Response, data: any): string => {
    if (response.status === 401) {
      return 'Session expired. Please log in again.';
    }
    if (response.status === 403) {
      return 'Access denied. You can only view your own reports.';
    }
    if (response.status === 404) {
      return data?.detail || 'No reports found.';
    }
    return data?.error || data?.detail || 'Failed to fetch reports.';
  }, []);

  /**
   * Fetch list of available reports
   */
  const fetchReportsList = useCallback(async () => {
    if (!authenticated) {
      setError('Please log in to view reports.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchWithAuth('/api/reports');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(handleError(response, data));
      }

      const typedData = data as ReportsListResponse;
      if (typedData.success && typedData.data) {
        setReportsList(typedData.data);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch reports';
      setError(message);
      setReportsList(null);
    } finally {
      setLoading(false);
    }
  }, [authenticated, fetchWithAuth, handleError]);

  /**
   * Fetch detailed daily report for a specific date
   */
  const fetchDailyReport = useCallback(async (date: string) => {
    if (!authenticated) {
      setError('Please log in to view reports.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchWithAuth(`/api/reports/${date}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(handleError(response, data));
      }

      const typedData = data as ReportDetailResponse;
      if (typedData.success && typedData.data) {
        setDailyReport(typedData.data);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch report';
      setError(message);
      setDailyReport(null);
    } finally {
      setLoading(false);
    }
  }, [authenticated, fetchWithAuth, handleError]);

  /**
   * Fetch user summary (all-time statistics)
   */
  const fetchUserSummary = useCallback(async () => {
    if (!authenticated) {
      setError('Please log in to view reports.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetchWithAuth('/api/reports/summary');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(handleError(response, data));
      }

      const typedData = data as UserSummaryResponse;
      if (typedData.success && typedData.data) {
        setUserSummary(typedData.data);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch summary';
      setError(message);
      setUserSummary(null);
    } finally {
      setLoading(false);
    }
  }, [authenticated, fetchWithAuth, handleError]);

  /**
   * Clear cached reports
   */
  const clearCache = useCallback(async () => {
    if (!authenticated) {
      return;
    }

    try {
      const response = await fetch(`${AUTH_URL}/api/reports/cache`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        // Refresh data after clearing cache
        setReportsList(null);
        setDailyReport(null);
        setUserSummary(null);
      }
    } catch (err) {
      console.error('Failed to clear cache:', err);
    }
  }, [authenticated]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    reportsList,
    dailyReport,
    userSummary,
    loading,
    error,
    fetchReportsList,
    fetchDailyReport,
    fetchUserSummary,
    clearCache,
    clearError,
  };
};
