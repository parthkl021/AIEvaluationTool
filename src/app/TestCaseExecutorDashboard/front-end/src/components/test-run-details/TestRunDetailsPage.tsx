import React, { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import styles from "./TestRunDetails.module.css";
import Modal from "./Modal";
import RunTimeline from "./RunTimeline";
import DetailCard from "../common/DetailCard/DetailCard";
import AppButton from "../common/Button/AppButton";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL, API_ENDPOINTS } from "../../config/api";

interface RunSummary {
  run_id: number;
  run_name: string;
  target: string | null;
  domain: string | null;
  status: string;
  start_ts: string;
  end_ts: string | null;
}

interface RunDetail {
  detail_id: number;
  run_name: string;
  testcase_name: string;
  metric_name: string;
  plan_name: string;
  conversation_id: string;
  status: string;
  score?: number | null;
}

interface FilterOption {
  filter_name: string;
}

interface AllFilters {
  metrics: FilterOption[];
  statuses: FilterOption[];
}

const RunDetails: React.FC = () => {
  const { runName } = useParams<{ runName: string }>();

  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [details, setDetails] = useState<RunDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null);
  const [executionDuration, setExecutionDuration] = useState<string | null>(null);
  const [filtersData, setFiltersData] = useState<AllFilters>({ metrics: [], statuses: [] });
  const [openFilterColumn, setOpenFilterColumn] = useState<string | null>(null);
  const filterRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const navigate = useNavigate();

  const [activeFilters, setActiveFilters] = useState<{ metric?: string; status?: string }>({});

  const statusMap = (status: string | null | undefined): "COMPLETED" | "RUNNING" | "FAILED" | undefined => {
    if (status === "COMPLETED" || status === "RUNNING" || status === "FAILED") return status;
    return undefined;
  };

  const handleFilterChange = (filterType: "metric" | "status", value: string) => {
    setActiveFilters((prev) => {
      if (!value) {
        const copy = { ...prev };
        delete copy[filterType];
        return copy;
      }
      return { ...prev, [filterType]: value };
    });
    setOpenFilterColumn(null);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openFilterColumn && filterRefs.current[openFilterColumn]) {
        const filterElement = filterRefs.current[openFilterColumn];
        if (filterElement && !filterElement.contains(event.target as Node)) {
          setOpenFilterColumn(null);
        }
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openFilterColumn]);

  useEffect(() => {
    fetch(`${API_BASE_URL}${API_ENDPOINTS.GET_ALL_FILTERS}`)
      .then((res) => res.json())
      .then((data) => setFiltersData({ metrics: data.metrics, statuses: data.statuses }))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!runName) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (activeFilters.metric) params.append("metric", activeFilters.metric);
    if (activeFilters.status) params.append("status", activeFilters.status);

    fetch(API_ENDPOINTS.GET_TEST_RUN_DETAILS(runName, params.toString()))
      .then((res) => {
        if (!res.ok) throw new Error(`API ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setSummary(data.summary);
        setDetails(data.details);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [runName, activeFilters]);

  if (loading) return <p className={styles.loading}>Loading test run...</p>;
  if (error) return <p className={styles.error}>{error}</p>;
  if (!summary) return <p>No test run found</p>;

  const groupedByPlan = details.reduce((acc, detail) => {
    if (!acc[detail.plan_name]) acc[detail.plan_name] = [];
    acc[detail.plan_name].push(detail);
    return acc;
  }, {} as Record<string, RunDetail[]>);

  return (
    <div className={styles.container}>
      <h3 className={styles.header}>Test Run Details - <span>{summary.run_name}</span></h3>

      <div className={styles.flex}>
        <div className={styles.summaryCard}>
          <h1 className={styles.title}>{summary.run_name}</h1>
          <div>
            <DetailCard label="Target" value={summary.target ?? "-"} icon="bi-bullseye" />
            <DetailCard label="Domain" value={summary.domain ?? "-"} icon="bi-globe" />
            <DetailCard label="Status" value={summary.status} status={statusMap(summary.status)} icon="bi-activity" />
            <DetailCard label="Started At" value={new Date(summary.start_ts).toLocaleString()} icon="bi-calendar-event" />
            <DetailCard label="Ended At" value={summary.end_ts ? new Date(summary.end_ts).toLocaleString() : "-"} icon="bi-calendar-check" />
            <DetailCard label="Duration" value={executionDuration ?? "-"} icon="bi-clock" />
          </div>
        </div>

        <div className={styles.tableLayout}>
          {/* Continue Button */}
          <div className={styles.filtersContainer}>
            <div className={styles.filtersCard} />
            <div>
              <AppButton
                label="Continue"
                variant="outline-secondary"
                icon="bi-play-fill"
                size="md"
                className="new-test-run-btn"
                onClick={() => navigate(`/continue-run/${runName}`)}
              />
            </div>
          </div>

          {/* Table */}
          <section className={styles.tableSection}>
            <div className={styles.tableContainer}>
              <div className="table-responsive">
                <table className={styles.resultsTable}>
                  <thead>
                    <tr>
                      <th>Plan Name</th>
                      <th>Test Case</th>

                      {/* Metric Column with Filter */}
                      <th>
                        <div className="header-content">
                          <span>Metric</span>
                          <div className="filter-wrapper" ref={(el) => { filterRefs.current["metric"] = el; }}>
                            <button
                              className="filter-trigger"
                              onClick={() => setOpenFilterColumn(openFilterColumn === "metric" ? null : "metric")}
                            >
                              <i className={`bi bi-funnel${activeFilters.metric ? "-fill" : ""}`}></i>
                            </button>
                            {openFilterColumn === "metric" && (
                              <div className="filter-dropdown">
                                <div className="filter-options">
                                  <select
                                    className="form-select form-select-sm"
                                    value={activeFilters.metric || ""}
                                    onChange={(e) => handleFilterChange("metric", e.target.value)}
                                  >
                                    <option value="">All Metrics</option>
                                    {filtersData.metrics.map((opt) => (
                                      <option key={opt.filter_name} value={opt.filter_name}>{opt.filter_name}</option>
                                    ))}
                                  </select>
                                  {activeFilters.metric && (
                                    <button className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("metric", "")}>
                                      Clear Filter
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </th>

                      <th>Score</th>

                      {/* Status Column with Filter */}
                      <th>
                        <div className="header-content">
                          <span>Status</span>
                          <div className="filter-wrapper" ref={(el) => { filterRefs.current["status"] = el; }}>
                            <button
                              className="filter-trigger"
                              onClick={() => setOpenFilterColumn(openFilterColumn === "status" ? null : "status")}
                            >
                              <i className={`bi bi-funnel${activeFilters.status ? "-fill" : ""}`}></i>
                            </button>
                            {openFilterColumn === "status" && (
                              <div className="filter-dropdown">
                                <div className="filter-options">
                                  <select
                                    className="form-select form-select-sm"
                                    value={activeFilters.status || ""}
                                    onChange={(e) => handleFilterChange("status", e.target.value)}
                                  >
                                    <option value="">All Statuses</option>
                                    {filtersData.statuses.map((opt) => (
                                      <option key={opt.filter_name} value={opt.filter_name}>{opt.filter_name}</option>
                                    ))}
                                  </select>
                                  {activeFilters.status && (
                                    <button className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("status", "")}>
                                      Clear Filter
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {details.length === 0 ? (
                      <tr>
                        <td colSpan={5} className={styles.emptyState}>No test case details found</td>
                      </tr>
                    ) : (
                      Object.entries(groupedByPlan).flatMap(([planName, planDetails]) =>
                        planDetails.map((d, index) => {
                          const normalizedStatus = d.status.toUpperCase();
                          const statusClass =
                            normalizedStatus === "COMPLETED" || normalizedStatus === "SUCCESS"
                              ? styles.statusCompleted
                              : normalizedStatus === "FAILED"
                              ? styles.statusFailed
                              : normalizedStatus === "NEW"
                              ? styles.statusNew
                              : styles.statusRunning;

                          return (
                            <tr
                              key={d.detail_id}
                              role="button"
                              className={`${styles.tableRow} ${hoveredMetric === d.metric_name ? styles.metricRowHover : ""}`}
                              data-bs-toggle="modal"
                              data-bs-target="#conversationModal"
                              onClick={() => setSelectedConversationId(Number(d.conversation_id))}
                              onMouseEnter={() => setHoveredMetric(d.metric_name)}
                              onMouseLeave={() => setHoveredMetric(null)}
                            >
                              {index === 0 && (
                                <td rowSpan={planDetails.length} className={`${styles.planCell} align-middle text-center`}>
                                  {planName}
                                </td>
                              )}
                              <td>{d.testcase_name}</td>
                              <td>{d.metric_name}</td>
                              <td>{d.score ?? "-"}</td>
                              <td>
                                <span className={`${styles.statusCell} ${statusClass}`}>{normalizedStatus}</span>
                              </td>
                            </tr>
                          );
                        })
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <RunTimeline
            runName={summary.run_name}
            hoveredMetric={hoveredMetric}
            hoveredPlan={hoveredPlan}
            onHoverPlan={setHoveredPlan}
            onHoverMetric={setHoveredMetric}
            onDurationCalculated={setExecutionDuration}
          />
        </div>
      </div>

      <Modal conversationId={selectedConversationId} />
    </div>
  );
};

export default RunDetails;