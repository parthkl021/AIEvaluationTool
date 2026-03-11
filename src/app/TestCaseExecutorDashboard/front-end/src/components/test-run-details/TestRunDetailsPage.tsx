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
  const [selectedDetailId, setSelectedDetailId] = useState<number | null>(null);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [hoveredPlan, setHoveredPlan] = useState<string | null>(null);
  const [executionDuration, setExecutionDuration] = useState<string | null>(null);
  const [filtersData, setFiltersData] = useState<AllFilters>({ metrics: [], statuses: [] });
  const [openFilterColumn, setOpenFilterColumn] = useState<string | null>(null);
  const [showScrollHint, setShowScrollHint] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(false);

  const [cardHeight, setCardHeight] = useState<number | null>(null);
  const summaryCardRef = useRef<HTMLDivElement | null>(null);
  const tableScrollRef = useRef<HTMLDivElement | null>(null);
  const filterRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const navigate = useNavigate();

  const [activeFilters, setActiveFilters] = useState<{ metric?: string; status?: string }>({});

  // Measure left card height via ResizeObserver — table matches this exactly
  useEffect(() => {
    const measure = () => {
      if (summaryCardRef.current) {
        setCardHeight(summaryCardRef.current.offsetHeight);
      }
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (summaryCardRef.current) ro.observe(summaryCardRef.current);
    return () => ro.disconnect();
  }, [summary, executionDuration]);

  const statusMap = (
    status: string | null | undefined
  ): "COMPLETED" | "RUNNING" | "FAILED" | undefined => {
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
    const updateScrollHint = () => {
      const node = tableScrollRef.current;
      if (!node) {
        setShowScrollHint(false);
        setIsAtBottom(false);
        return;
      }
      setShowScrollHint(node.scrollHeight > node.clientHeight + 2);
      const maxScrollTop = node.scrollHeight - node.clientHeight;
      setIsAtBottom(node.scrollTop >= maxScrollTop - 2);
    };
    updateScrollHint();
    window.addEventListener("resize", updateScrollHint);
    return () => window.removeEventListener("resize", updateScrollHint);
  }, [details, cardHeight]);

  useEffect(() => {
    const node = tableScrollRef.current;
    if (!node) return;
    const onScroll = () => {
      const maxScrollTop = node.scrollHeight - node.clientHeight;
      setIsAtBottom(node.scrollTop >= maxScrollTop - 2);
    };
    node.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => node.removeEventListener("scroll", onScroll);
  }, [details]);

  useEffect(() => {
    const clearSelectionIfConversationModal = (event: Event) => {
      const target = event.target as HTMLElement | null;
      if (target?.id !== "conversationModal") return;
      setSelectedConversationId(null);
      setSelectedDetailId(null);
    };

    // Use document-level listener so it still works even if Bootstrap replaces/rehydrates modal DOM.
    document.addEventListener(
      "hide.bs.modal",
      clearSelectionIfConversationModal as EventListener
    );
    document.addEventListener(
      "hidden.bs.modal",
      clearSelectionIfConversationModal as EventListener
    );
    return () => {
      document.removeEventListener(
        "hide.bs.modal",
        clearSelectionIfConversationModal as EventListener
      );
      document.removeEventListener(
        "hidden.bs.modal",
        clearSelectionIfConversationModal as EventListener
      );
    };
  }, []);

  const handleScrollChevronClick = () => {
    const node = tableScrollRef.current;
    if (!node) return;
    if (isAtBottom) {
      node.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
    }
  };

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

  const tableContainerHeight = cardHeight ?? undefined;

  return (
    <div className={styles.container}>
      <RunTimeline
        runName={summary.run_name}
        hoveredMetric={hoveredMetric}
        hoveredPlan={hoveredPlan}
        onHoverPlan={setHoveredPlan}
        onHoverMetric={setHoveredMetric}
        onDurationCalculated={setExecutionDuration}
      />

      <div className={styles.flex}>
        {/* ── LEFT CARD — natural height, drives table height ── */}
        <div className={styles.summaryCard} ref={summaryCardRef}>
          <div className={styles.summaryContent}>
            <DetailCard label="Target" value={summary.target ?? "-"} icon="bi-bullseye" />
            <DetailCard label="Domain" value={summary.domain ?? "-"} icon="bi-globe" />
            <DetailCard
              label="Status"
              value={summary.status}
              status={statusMap(summary.status)}
              icon="bi-activity"
            />
            <DetailCard
              label="Started At"
              value={new Date(summary.start_ts).toLocaleString()}
              icon="bi-calendar-event"
            />
            <DetailCard
              label="Ended At"
              value={summary.end_ts ? new Date(summary.end_ts).toLocaleString() : "-"}
              icon="bi-calendar-check"
            />
            <DetailCard
              label="Duration"
              value={executionDuration ?? "-"}
              icon="bi-clock"
            />
            {/* Continue button — inside card, pinned to bottom */}
            <div className={styles.actionsRow}>
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
        </div>

        {/* ── RIGHT TABLE — height locked to left card height ── */}
        <div className={styles.tableLayout}>
          <section className={styles.tableSection}>
            <div
              className={`${styles.tableContainer}${isAtBottom ? ` ${styles.atBottom}` : ""}`}
              style={tableContainerHeight ? { height: tableContainerHeight } : undefined}
            >
              <div
                ref={tableScrollRef}
                className={`${styles.tableScroll} table-responsive`}
                style={tableContainerHeight ? { height: tableContainerHeight } : undefined}
              >
                <table className={styles.resultsTable}>
                  <thead>
                    <tr>
                      <th>Plan Name</th>
                      <th>Test Case</th>

                      {/* Metric Column with Filter */}
                      <th>
                        <div className="header-content">
                          <span>Metric</span>
                          <div
                            className="filter-wrapper"
                            ref={(el) => { filterRefs.current["metric"] = el; }}
                          >
                            <button
                              className="filter-trigger"
                              onClick={() =>
                                setOpenFilterColumn(openFilterColumn === "metric" ? null : "metric")
                              }
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
                                      <option key={opt.filter_name} value={opt.filter_name}>
                                        {opt.filter_name}
                                      </option>
                                    ))}
                                  </select>
                                  {activeFilters.metric && (
                                    <button
                                      className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("metric", "")}
                                    >
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
                          <div
                            className="filter-wrapper"
                            ref={(el) => { filterRefs.current["status"] = el; }}
                          >
                            <button
                              className="filter-trigger"
                              onClick={() =>
                                setOpenFilterColumn(openFilterColumn === "status" ? null : "status")
                              }
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
                                      <option key={opt.filter_name} value={opt.filter_name}>
                                        {opt.filter_name}
                                      </option>
                                    ))}
                                  </select>
                                  {activeFilters.status && (
                                    <button
                                      className="btn btn-sm btn-outline-secondary mt-2 w-100"
                                      onClick={() => handleFilterChange("status", "")}
                                    >
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
                        <td colSpan={5} className={styles.emptyState}>
                          No test case details found
                        </td>
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
                              tabIndex={0}
                              aria-pressed={selectedDetailId === d.detail_id}
                              className={`${styles.tableRow} ${
                                hoveredMetric === d.metric_name ? styles.metricRowHover : ""
                              } ${selectedDetailId === d.detail_id ? styles.selectedRow : ""}`}
                              data-bs-toggle="modal"
                              data-bs-target="#conversationModal"
                              onClick={() => {
                                setSelectedConversationId(Number(d.conversation_id));
                                setSelectedDetailId(d.detail_id);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  setSelectedConversationId(Number(d.conversation_id));
                                  setSelectedDetailId(d.detail_id);
                                }
                              }}
                              onMouseEnter={() => setHoveredMetric(d.metric_name)}
                              onMouseLeave={() => setHoveredMetric(null)}
                            >
                              {index === 0 && (
                                <td
                                  rowSpan={planDetails.length}
                                  className={`${styles.planCell} align-middle text-center`}
                                >
                                  {planName}
                                </td>
                              )}
                              <td>{d.testcase_name}</td>
                              <td>{d.metric_name}</td>
                              <td>{d.score ?? "-"}</td>
                              <td>
                                <span className={`${styles.statusCell} ${statusClass}`}>
                                  {normalizedStatus}
                                </span>
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

            {/* Single chevron below the table */}
            {showScrollHint && (
              <div className={styles.scrollChevronRow}>
                <button
                  type="button"
                  className={`${styles.scrollChevron}${isAtBottom ? ` ${styles.atBottom}` : ""}`}
                  onClick={handleScrollChevronClick}
                  aria-label={isAtBottom ? "Scroll to top" : "Scroll to bottom"}
                  title={isAtBottom ? "Scroll to top" : "Scroll to bottom"}
                >
                  <span className={styles.scrollChevronIcons} aria-hidden="true">
                    <i
                      className={`bi ${
                        isAtBottom ? "bi-chevron-double-up" : "bi-chevron-double-down"
                      } ${styles.scrollChevronIcon}`}
                    />
                    <i
                      className={`bi ${
                        isAtBottom ? "bi-chevron-double-up" : "bi-chevron-double-down"
                      } ${styles.scrollChevronIcon} ${styles.scrollChevronIcon2}`}
                    />
                  </span>
                </button>
              </div>
            )}
          </section>
        </div>
      </div>

      <Modal conversationId={selectedConversationId} />
    </div>
  );
};

export default RunDetails;
