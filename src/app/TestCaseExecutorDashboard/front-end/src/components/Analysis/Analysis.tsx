import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { API_ENDPOINTS, WS_BASE_URL } from "../../config/api";
import styles from "./Analysis.module.css";

interface RunSummary {
  run_name: string;
  status: string;
  start_ts: string;
  end_ts: string | null;
}

interface RunDetail {
  detail_id: number;
  testcase_name: string;
  metric_name: string;
  strategy_name?: string;
  status: string;
  score?: number | null;
}

interface TestRunResponse {
  summary: RunSummary;
  details: RunDetail[];
}

interface AnalyseStatusResponse {
  run_name: string;
  status: string;
  current?: number;
  total?: number;
  analysis_start_ts?: string;
  analysis_end_ts?: string;
  analysis_duration_seconds?: number;
  error?: string;
}

interface AnalysisProgressMessage {
  type: string;
  runName: string;
  current?: number;
  total?: number;
  testcaseName?: string;
  metricName?: string;
  strategyName?: string;
  detailId?: number;
  score?: number | null;
  analysisStartTs?: string;
  analysisEndTs?: string;
  error?: string;
}

const toFiniteNumber = (value: unknown): number | null => {
  if (value === null || value === undefined || value === "") return null;
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numeric) ? numeric : null;
};

const formatDuration = (start: string, end: string | null): string => {
  if (!start || !end) return "-";
  const startMs = new Date(start).getTime();
  const endMs = new Date(end).getTime();
  if (Number.isNaN(startMs) || Number.isNaN(endMs) || endMs < startMs) return "-";

  const totalSeconds = Math.floor((endMs - startMs) / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
};

const Analysis: React.FC = () => {
  const { runName } = useParams<{ runName: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState<boolean>(true);
  const [isAnalysing, setIsAnalysing] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [analysisStartTs, setAnalysisStartTs] = useState<string | null>(null);
  const [analysisEndTs, setAnalysisEndTs] = useState<string | null>(null);
  const [analysisCurrent, setAnalysisCurrent] = useState<number>(0);
  const [analysisTotal, setAnalysisTotal] = useState<number>(0);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null);
  const [liveProgress, setLiveProgress] = useState<AnalysisProgressMessage | null>(null);

  const orderedDetails = useMemo(
    () => [...details].sort((a, b) => a.detail_id - b.detail_id),
    [details]
  );
  const orderedDetailsRef = useRef<RunDetail[]>([]);

  useEffect(() => {
    orderedDetailsRef.current = orderedDetails;
  }, [orderedDetails]);

  const fetchDetails = async (targetRunName: string, silent = false): Promise<void> => {
    const detailsRes = await fetch(API_ENDPOINTS.GET_TEST_RUN_DETAILS(targetRunName, ""));
    if (!detailsRes.ok) {
      const detailsBody = await detailsRes.json().catch(() => null);
      throw new Error(detailsBody?.detail || `Failed to load run details (${detailsRes.status})`);
    }
    const data: TestRunResponse = await detailsRes.json();
    setSummary(data.summary);
    setDetails(data.details || []);
    if (!silent) {
      setLoading(false);
    }
  };

  const applyProgress = useCallback((payload: AnalysisProgressMessage) => {
    setLiveProgress(payload);
    if (payload.analysisStartTs) {
      setAnalysisStartTs(payload.analysisStartTs);
    }
    if (payload.analysisEndTs) {
      setAnalysisEndTs(payload.analysisEndTs);
    }

    const detailId = toFiniteNumber(payload.detailId);
    const current = toFiniteNumber(payload.current);
    const total = toFiniteNumber(payload.total);
    const score = toFiniteNumber(payload.score);

    if (current !== null) {
      setAnalysisCurrent(current);
    }
    if (total !== null) {
      setAnalysisTotal(total);
    }

    if (detailId !== null) {
      const idx = orderedDetailsRef.current.findIndex((d) => d.detail_id === detailId);
      if (idx >= 0) {
        setCurrentStepIndex(idx);
      }
    } else if (current !== null && current > 0) {
      setCurrentStepIndex(Math.max(0, current - 1));
    }

    if (score !== null && detailId !== null) {
      setDetails((prev) =>
        prev.map((d) => (d.detail_id === detailId ? { ...d, score } : d))
      );
    }
  }, []);

  useEffect(() => {
    if (!runName) {
      setError("Run name is missing in the URL.");
      setLoading(false);
      return;
    }

    let isMounted = true;
    let statusTimer: number | null = null;
    let keepAliveTimer: number | null = null;
    let ws: WebSocket | null = null;

    const pollStatus = async () => {
      const statusRes = await fetch(API_ENDPOINTS.ANALYSE_RUN_STATUS(runName));
      if (!statusRes.ok) {
        return;
      }
      const statusData: AnalyseStatusResponse = await statusRes.json();
      if (!isMounted) return;

      if (statusData.analysis_start_ts) setAnalysisStartTs(statusData.analysis_start_ts);
      if (statusData.analysis_end_ts) setAnalysisEndTs(statusData.analysis_end_ts);

      const polledCurrent = toFiniteNumber(statusData.current);
      const polledTotal = toFiniteNumber(statusData.total);
      if (polledCurrent !== null || polledTotal !== null) {
        applyProgress({
          type: "ANALYSIS_PROGRESS",
          runName,
          current: polledCurrent ?? undefined,
          total: polledTotal ?? undefined,
          analysisStartTs: statusData.analysis_start_ts,
          analysisEndTs: statusData.analysis_end_ts,
        });
      }

      if (statusData.status === "RUNNING") {
        setIsAnalysing(true);
        setIsCompleted(false);
      } else if (statusData.status === "COMPLETED") {
        setIsAnalysing(false);
        setIsCompleted(true);
        await fetchDetails(runName, true);
        if (orderedDetailsRef.current.length > 0) {
          const last = orderedDetailsRef.current.length - 1;
          setCurrentStepIndex(last);
          setSelectedStepIndex(last);
        }
        if (statusTimer) {
          window.clearInterval(statusTimer);
          statusTimer = null;
        }
      } else if (statusData.status === "FAILED") {
        setIsAnalysing(false);
        setError(statusData.error || "Analysis failed.");
        if (statusTimer) {
          window.clearInterval(statusTimer);
          statusTimer = null;
        }
      }
    };

    const startAnalysis = async () => {
      try {
        setError(null);
        await fetchDetails(runName);

        const analyseRes = await fetch(API_ENDPOINTS.ANALYSE_RUN(runName));
        if (!analyseRes.ok) {
          const analyseBody = await analyseRes.json().catch(() => null);
          throw new Error(analyseBody?.detail || `Analysis failed (${analyseRes.status})`);
        }

        const analyseData = await analyseRes.json().catch(() => ({ status: "started" }));
        if (!isMounted) return;
        setIsAnalysing(analyseData.status === "started" || analyseData.status === "running");
        setIsCompleted(false);
        setLoading(false);

        ws = new WebSocket(`${WS_BASE_URL}/ws/test-run`);
        ws.onopen = () => {
          ws?.send(JSON.stringify({ type: "ANALYSIS_SUBSCRIBE", runName }));
          keepAliveTimer = window.setInterval(() => {
            ws?.send("ping");
          }, 15000);
        };

        ws.onmessage = async (event) => {
          if (!isMounted) return;
          let payload: AnalysisProgressMessage | null = null;
          try {
            payload = JSON.parse(event.data);
          } catch {
            return;
          }
          if (!payload || payload.runName !== runName) return;

          if (payload.type === "ANALYSIS_STARTED") {
            setIsAnalysing(true);
            setIsCompleted(false);
            applyProgress(payload);
            return;
          }

          if (payload.type === "ANALYSIS_PROGRESS") {
            applyProgress(payload);
            return;
          }

          if (payload.type === "ANALYSIS_FINISHED") {
            setIsAnalysing(false);
            setIsCompleted(true);
            applyProgress(payload);
            await fetchDetails(runName, true);
            if (orderedDetailsRef.current.length > 0) {
              const last = orderedDetailsRef.current.length - 1;
              setCurrentStepIndex(last);
              setSelectedStepIndex(last);
            }
            return;
          }

          if (payload.type === "ANALYSIS_FAILED") {
            setIsAnalysing(false);
            setError(payload.error || "Analysis failed.");
            if (statusTimer) {
              window.clearInterval(statusTimer);
              statusTimer = null;
            }
          }
        };
      } catch (e) {
        if (isMounted) {
          setError(e instanceof Error ? e.message : "Something went wrong while analysing this run.");
          setLoading(false);
          setIsAnalysing(false);
        }
      }
    };

    startAnalysis();
    pollStatus();
    statusTimer = window.setInterval(pollStatus, 2000);

    return () => {
      isMounted = false;
      if (statusTimer) {
        window.clearInterval(statusTimer);
      }
      if (keepAliveTimer) {
        window.clearInterval(keepAliveTimer);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [runName, applyProgress]);

  useEffect(() => {
    if (!isCompleted) {
      setSelectedStepIndex(currentStepIndex);
      return;
    }
    if (orderedDetails.length === 0) {
      setSelectedStepIndex(null);
      return;
    }
    setSelectedStepIndex((prev) => {
      if (prev === null) return orderedDetails.length - 1;
      return Math.min(prev, orderedDetails.length - 1);
    });
  }, [isCompleted, orderedDetails.length, currentStepIndex]);

  const stats = useMemo(() => {
    const scoredItems = orderedDetails.filter((d) => typeof d.score === "number") as Array<RunDetail & { score: number }>;
    const totalScore = scoredItems.reduce((sum, d) => sum + d.score, 0);
    const overallScore = scoredItems.length > 0 ? totalScore / scoredItems.length : null;
    const totalCases = analysisTotal > 0 ? analysisTotal : orderedDetails.length;
    const completed = Math.max(0, Math.min(analysisCurrent, totalCases));

    return {
      totalCases,
      completedCases: completed,
      overallScore,
    };
  }, [orderedDetails, analysisCurrent, analysisTotal]);

  const displayedStepIndex = isCompleted
    ? selectedStepIndex ?? Math.max(orderedDetails.length - 1, 0)
    : currentStepIndex;
  const currentStep = orderedDetails[displayedStepIndex] ?? null;
  const progressPercent = orderedDetails.length > 0
    ? Math.round(((Math.min(currentStepIndex + 1, orderedDetails.length)) / orderedDetails.length) * 100)
    : 0;

  if (loading) return <div className={styles.state}>Running analysis for this run...</div>;
  if (error) return <div className={`${styles.state} ${styles.error}`}>{error}</div>;
  if (!summary) return <div className={styles.state}>No analysis data found.</div>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2>Run Analysis</h2>
        {isAnalysing && <p>Analysis is running. Live execution loop is updating...</p>}
        {isCompleted && <p className={styles.success}>Completed successfully.</p>}
      </div>

      <section className={styles.cardGrid}>
        <div className={styles.card}>
          <span className={styles.label}>Run Name</span>
          <span className={styles.value}>{summary.run_name}</span>
        </div>

        <div className={styles.card}>
          <span className={styles.label}>Duration</span>
          <span className={styles.value}>
            {formatDuration(analysisStartTs || "", analysisEndTs)}
          </span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Overall Score</span>
          <span className={styles.value}>
            {stats.overallScore !== null ? stats.overallScore.toFixed(2) : "-"}
          </span>
        </div>
        <div className={styles.card}>
          <span className={styles.label}>Completed / Total</span>
          <span className={styles.value}>{stats.completedCases} / {stats.totalCases}</span>
        </div>
      </section>

      <section className={styles.executionWrap}>
        <div className={styles.executionHeaderRow}>
          <h3>Execution Loop</h3>
          {orderedDetails.length > 0 && (
            <span className={styles.executionCount}>Step {Math.min(displayedStepIndex + 1, orderedDetails.length)} / {orderedDetails.length}</span>
          )}
        </div>

        {currentStep ? (
          <>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progressPercent}%` }} />
            </div>

            <div className={styles.currentStepCard}>
              <div className={styles.stepLabel}>Current Strategy</div>
              <div className={styles.stepValue}>
                {isCompleted
                  ? currentStep.strategy_name || "Strategy"
                  : liveProgress?.strategyName || currentStep.strategy_name || "Strategy"}
              </div>

              <div className={styles.stepMetaGrid}>
                <div>
                  <span className={styles.metaLabel}>Metric</span>
                  <span className={styles.metaValue}>{isCompleted ? currentStep.metric_name : liveProgress?.metricName || currentStep.metric_name}</span>
                </div>
                <div>
                  <span className={styles.metaLabel}>Test Case</span>
                  <span className={styles.metaValue}>{isCompleted ? currentStep.testcase_name : liveProgress?.testcaseName || currentStep.testcase_name}</span>
                </div>
                <div>
                  <span className={styles.metaLabel}>Status</span>
                  <span className={styles.metaValue}>{isCompleted ? "COMPLETED" : isAnalysing ? "RUNNING" : currentStep.status}</span>
                </div>
                <div>
                  <span className={styles.metaLabel}>Score</span>
                  <span className={styles.metaValue}>
                    {typeof liveProgress?.score === "number" && !isCompleted
                      ? liveProgress.score.toFixed(2)
                      : typeof currentStep.score === "number"
                        ? currentStep.score.toFixed(2)
                        : "-"}
                  </span>
                </div>
              </div>
            </div>

            <div className={styles.stepRail}>
              {orderedDetails.map((item, index) => {
                const stateClass = isCompleted
                  ? index === displayedStepIndex
                    ? styles.stepSelected
                    : styles.stepDone
                  : index < currentStepIndex
                    ? styles.stepDone
                    : index === currentStepIndex
                      ? styles.stepActive
                      : styles.stepPending;

                return (
                  <button
                    key={item.detail_id}
                    type="button"
                    className={`${styles.stepChip} ${stateClass} ${isCompleted ? styles.stepChipClickable : ""}`}
                    onClick={() => {
                      if (isCompleted) {
                        setSelectedStepIndex(index);
                      }
                    }}
                  >
                    <span className={styles.chipStrategy}>{item.strategy_name || "Strategy"}</span>
                    <span className={styles.chipMetric}>{item.metric_name}</span>
                    <span className={styles.chipCase}>{item.testcase_name}</span>
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          <div className={styles.empty}>No analysed test case records found.</div>
        )}
      </section>

      {isCompleted && (
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.routeButton}
            onClick={() => navigate(`/test-runs/${encodeURIComponent(summary.run_name)}`)}
          >
            Go to /test-runs/{summary.run_name}
          </button>
        </div>
      )}
    </div>
  );
};

export default Analysis;
