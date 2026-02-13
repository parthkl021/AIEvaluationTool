import React, { useEffect, useState } from "react";
import "./Filters.css";
import { AllFilters } from "../../types/Filters";
import FilterSelect from "../common/Filters/Filters";
import AppButton from "../common/Button/AppButton";
import { useNavigate } from "react-router-dom";

interface FiltersProps {
  onFilterChange?: (filterType: string, value: string) => void;
}

const Filters: React.FC<FiltersProps> = ({ onFilterChange }) => {
  const [filters, setFilters] = useState<AllFilters>({
    domains: [],
    languages: [],
    targets: [],
    plans: [],
    metrics: [],
    statuses: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        setIsLoading(true);
        const res = await fetch("http://localhost:7000/get_all_filters");
        if (!res.ok) throw new Error("Failed to fetch");
        const data = await res.json();
        setFilters(data);
      } catch (err) {
        console.error("Error fetching filters:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchFilters();
  }, []);

  const filterConfigs = [
    { type: "domain", label: "Domain", options: filters.domains },
    { type: "target", label: "Target", options: filters.targets },
    { type: "status", label: "Status", options: filters.statuses },
  ];

  return (
    <div className={`filtersContainer ${isLoading ? 'isFetching' : ''}`}>
      <div className="filtersList">
        {filterConfigs.map((config) => (
          <div key={config.type} className="filterWrapper withIcon">
            {/* This SVG now sits inside the wrapper */}
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2.5" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="innerFilterIcon"
            >
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            <FilterSelect
              filterType={config.type}
              placeholder={config.label}
              options={config.options}
              isLoading={isLoading}
              onChange={onFilterChange}
            />
          </div>
        ))}

      </div>
      <div className="header-content">
        <div className="header-actions">
          <AppButton
            label="Continue"
            variant="outline-secondary"
            icon="bi-play-fill"
            size="md"
            className="continue-btn"
          />
          <AppButton
            label="New Test Run"
            variant="primary"
            icon="bi-plus-lg"
            size="md"
            className="new-test-run-btn"
            onClick={() => navigate(`/create-test-run`)}
          />
        </div>
      </div>

    </div>
  );
};

export default Filters;