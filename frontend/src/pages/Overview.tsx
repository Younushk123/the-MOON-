
import React, { useState } from "react";
import {
  ClipboardList,
  Atom,
  CircleDot,
  Database,
  ArrowRight,
  Search,
  Flame,
} from "lucide-react";

import "../styles/overview.css";

import MockNotice from "../components/ui/MockNotice";
import { formatDate, formatRange } from "../utils/format";
import { getStatusMeta } from "../utils/status";
import type { AnalysisResult } from "../types/schemas";

import earthSpace from "../assets/earth-space.png";
import combustionFlame from "../assets/combustion-flame.png";

type Experiment = {
  id: string;
  title: string;
  conditions?: string;
  source?: string;
  status: string;
  [key: string]: any;
};

type OverviewProps = {
  experiments: Experiment[];
  analyses?: AnalysisResult[];
  setPage: (page: string) => void;
  setSelected: (experiment: Experiment) => void;
};

type StatCardProps = {
  icon: React.ElementType;
  title: string;
  value: string;
  detail: string;
  onOpen: () => void;
};

function StatCard({
  icon: Icon,
  title,
  value,
  detail,
  onOpen,
}: StatCardProps) {
  return (
    <article
      className="overview-stat-card"
      role="button"
      tabIndex={0}
      aria-label={`Open ${title}`}
      onClick={onOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen();
        }
      }}
      title={`Open ${title}`}
    >
      <div className="overview-stat-icon">
        <Icon size={23} />
      </div>

      <div className="overview-stat-info">
        <p>{title}</p>
        <h3>{value}</h3>
        <span>{detail}</span>
      </div>
    </article>
  );
}

type RecentExperimentsProps = {
  experiments: Experiment[];
  onView: (experiment: Experiment) => void;
};

function RecentExperiments({
  experiments,
  onView,
}: RecentExperimentsProps) {
  const [search, setSearch] = useState("");

  const filteredExperiments = experiments.filter((item) =>
    [
      item.id,
      item.title,
      item.conditions ?? "",
      item.source ?? "",
      item.status,
    ].some((value) =>
      String(value).toLowerCase().includes(search.toLowerCase())
    )
  );

  return (
    <section className="overview-experiments" id="recent-experiments">
      <div className="overview-section-heading">
        <div>
          <h2>Recent Experiments</h2>
          <p>Latest microgravity combustion experiments</p>
        </div>

        <span className="overview-count">
          {filteredExperiments.length} records
        </span>
      </div>

      <div className="overview-table-search">
        <Search size={16} />

        <input
          type="text"
          placeholder="Search experiments..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          aria-label="Search experiments"
        />
      </div>

      <div className="overview-table-container">
        <table className="overview-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Conditions</th>
              <th>Source</th>
              <th>Status</th>
              <th>View</th>
            </tr>
          </thead>

          <tbody>
            {filteredExperiments.map((item) => (
              <tr key={item.id}>
                <td className="overview-experiment-id">{item.id}</td>

                <td className="overview-experiment-name">
                  {item.title}
                </td>

                <td>
                  {item.conditions ??
                    `T: ${formatRange(item.temperatureMin ?? null, item.temperatureMax ?? null, "K")} | P: ${formatRange(item.pressure ?? null, item.pressureMax ?? null, "atm")}`}
                </td>

                <td>{item.source || "Unknown"}</td>

                <td>
                  <span
                    className={`overview-status ${
                      getStatusMeta(item.statusKey ?? item.status).tone ===
                      "validated"
                        ? "validated"
                        : "review"
                    }`}
                  >
                    {item.status}
                  </span>
                </td>

                <td>
                  <button
                    type="button"
                    className="overview-view-btn"
                    onClick={() => {
                      onView(item);
                    }}
                    aria-label={`View details for ${item.title}`}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}

            {filteredExperiments.length === 0 && (
              <tr>
                <td colSpan={6} className="overview-empty">
                  No experiments found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <MockNotice />
    </section>
  );
}

type ResearchCardProps = {
  onExplore: () => void;
};

function ResearchCard({ onExplore }: ResearchCardProps) {
  return (
    <aside className="overview-research-card">
      <div className="overview-research-image">
        <img
          src={combustionFlame}
          alt="Combustion flame experiment"
        />
      </div>

      <div className="overview-research-content">
        <span className="overview-eyebrow">
          <Flame size={14} />
          RESEARCH SPOTLIGHT
        </span>

        <h2>
          Smaller gravity.
          <br />
          Bigger questions.
        </h2>

        <p>
          Microgravity changes how flames behave. Explore combustion
          data to improve fire safety for future space missions.
        </p>

        <button
          type="button"
          className="overview-explore-btn"
          onClick={onExplore}
        >
          Explore Experiments
          <ArrowRight size={17} />
        </button>
      </div>
    </aside>
  );
}

export default function Overview({
  experiments,
  analyses = [],
  setPage,
  setSelected,
}: OverviewProps) {
  const openExperiment = (experiment: Experiment) => {
    setSelected(experiment);
    setPage("Details");
  };

 
  const conditionSets = new Set(
    experiments
      .filter((item) => item.conditionsLoaded && item.fuel != null)
      .map(
        (item) =>
          `${item.temperatureMin ?? ""}-${item.temperatureMax ?? ""}-${item.pressure ?? ""}-${item.fuel ?? ""}`
      )
  );

  const sourceCount = new Set(experiments.flatMap((item) => item.sourceIds ?? [])).size;

  const newest = experiments
    .map((item) => item.lastUpdated)
    .filter(Boolean)
    .sort()
    .at(-1);
  const lastUpdated = formatDate(newest);

  
  const passed = analyses.filter((a) => a.data_quality?.validation_passed).length;
  const analysisDetail = analyses.length
    ? `${passed} of ${analyses.length} analyses passed validation`
    : "View data quality";

  return (
    <div className="overview-page">
      <section className="overview-hero">
        <div
          className="overview-hero-background"
          style={{ backgroundImage: `url(${earthSpace})` }}
        />

        <div className="overview-hero-content">
          <span className="overview-hero-label">
            <span className="overview-live-dot" />
            MICROGRAVITY COMBUSTION RESEARCH
          </span>

          <h1>Welcome to THE MOON</h1>

          <p>
            Exploring microgravity combustion data with the power of AI.
          </p>
        </div>
      </section>

      <div className="overview-content">
        <section className="overview-stats-grid">
          <StatCard
            icon={ClipboardList}
            title="Total Experiments"
            value={String(experiments.length)}
            detail="View all experiment records"
            onOpen={() => setPage("Explorer")}
          />

          <StatCard
            icon={Atom}
            title="Unique Conditions"
            value={
              conditionSets.size > 0 ? String(conditionSets.size) : "—"
            }
            detail="Temperature, Pressure, Fuel"
            onOpen={() => setPage("Comparison")}
          />

          <StatCard
            icon={CircleDot}
            title="Data Sources"
            value={String(sourceCount)}
            detail="Referenced source IDs"
            onOpen={() => setPage("Data Quality")}
          />

          <StatCard
            icon={Database}
            title="Last Updated"
            value={lastUpdated}
            detail={analysisDetail}
            onOpen={() => setPage("Data Quality")}
          />
        </section>

        <div className="overview-main-grid">
          <RecentExperiments
            experiments={experiments}
            onView={openExperiment}
          />

          <ResearchCard onExplore={() => setPage("Explorer")} />
        </div>

        <footer className="overview-footer">
          THE MOON · AI-Powered Combustion Research
        </footer>
      </div>
    </div>
  );
}
