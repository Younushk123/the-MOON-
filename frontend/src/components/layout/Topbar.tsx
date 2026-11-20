
import {
  Bell,
  Search,
  UserCircle,
  Menu,
} from "lucide-react";

export default function Topbar({
  search,
  setSearch,
  setIsMobileOpen,
}) {
  return (
    <header className="topbar">
      <button
        type="button"
        className="mobile-menu-button"
        onClick={() => setIsMobileOpen((prev) => !prev)}
        aria-label="Open navigation menu"
        title="Menu"
      >
        <Menu size={24} />
      </button>

      <div className="topbar-brand">
        <div className="topbar-brand-text">
          <strong>THE MOON</strong>

          <span>
            AI-Powered Fire Safety Insights from Microgravity Combustion Data
          </span>
        </div>
      </div>

      <label className="global-search">
        <Search size={17} />

        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search experiments, keywords, or ID..."
          aria-label="Search experiments"
        />
      </label>

    </header>
  );
}
