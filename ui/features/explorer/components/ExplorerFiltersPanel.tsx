"use client";

import { Filter, RotateCcw, Search } from "lucide-react";

import type { ExplorerFilters } from "@/features/explorer/types/explorer";

export default function ExplorerFiltersPanel({
  filters,
  objectTypes,
  relationshipTypes,
  onChange,
  onReset,
}: {
  filters: ExplorerFilters;
  objectTypes: string[];
  relationshipTypes: string[];
  onChange: (filters: ExplorerFilters) => void;
  onReset: () => void;
}) {
  function toggle(list: string[], value: string) {
    return list.includes(value)
      ? list.filter((item) => item !== value)
      : [...list, value];
  }

  return (
    <aside className="explorer-filter-panel">
      <div className="explorer-panel-title">
        <span><Filter size={16} /></span>
        <div><strong>Graph filters</strong><small>Refine the enterprise view</small></div>
      </div>

      <label className="explorer-search-field">
        <Search size={15} aria-hidden="true" />
        <input
          value={filters.query}
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
          placeholder="Search objects…"
        />
      </label>

      <div className="explorer-filter-group">
        <div className="explorer-filter-label">
          <span>Minimum confidence</span>
          <strong>{Math.round(filters.minimumConfidence * 100)}%</strong>
        </div>
        <input
          aria-label="Minimum relationship confidence"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={filters.minimumConfidence}
          onChange={(event) => onChange({
            ...filters,
            minimumConfidence: Number(event.target.value),
          })}
        />
      </div>

      <FilterGroup
        title="Object types"
        values={objectTypes}
        selected={filters.objectTypes}
        onToggle={(value) => onChange({
          ...filters,
          objectTypes: toggle(filters.objectTypes, value),
        })}
      />

      <FilterGroup
        title="Relationship types"
        values={relationshipTypes}
        selected={filters.relationshipTypes}
        onToggle={(value) => onChange({
          ...filters,
          relationshipTypes: toggle(filters.relationshipTypes, value),
        })}
      />

      <button type="button" className="explorer-reset-button" onClick={onReset}>
        <RotateCcw size={14} /> Reset filters
      </button>
    </aside>
  );
}

function FilterGroup({
  title,
  values,
  selected,
  onToggle,
}: {
  title: string;
  values: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  if (!values.length) return null;

  return (
    <fieldset className="explorer-filter-group explorer-check-list">
      <legend>{title}</legend>
      {values.map((value) => (
        <label key={value}>
          <input
            type="checkbox"
            checked={selected.length === 0 || selected.includes(value)}
            onChange={() => onToggle(value)}
          />
          <span>{value.replaceAll("_", " ")}</span>
        </label>
      ))}
    </fieldset>
  );
}
