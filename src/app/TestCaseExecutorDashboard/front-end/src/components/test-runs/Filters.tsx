import React, { useEffect, useState } from "react";
import "./Filters.css";
import { AllFilters } from "../../types/Filters";
import FilterSelect from "../common/Filters/Filters"

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

  useEffect(() => {
    setIsLoading(true);
    fetch("http://localhost:7000/get_all_filters")
      .then((res) => res.json())
      .then((data: AllFilters) => {
        setFilters(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching filters:", err);
        setIsLoading(false);
      });
  }, []);

  return (
    <div className="filters">
      <FilterSelect
        filterType="domain"
        placeholder="Domain"
        options={filters.domains}
        isLoading={isLoading}
        onChange={onFilterChange}
      />

      {/* <FilterSelect
        placeholder="Language"
        filterType="language"
        options={filters.languages}
        isLoading={isLoading}
        onChange={onFilterChange}
      /> */}

      <FilterSelect
        placeholder="Target"
        filterType="target"
        options={filters.targets}
        isLoading={isLoading}
        onChange={onFilterChange}
      />
      <FilterSelect
        placeholder="Status"
        filterType="status"
        options={filters.statuses}
        isLoading={isLoading}
        onChange={onFilterChange}
      />
    </div>
  );
};

export default Filters;
