import React, { useEffect, useState } from "react";
import "../styles/Settings.css";

const defaultSettings = {
  displayName: "Researcher",
  defaultPage: "Overview",
  defaultStatus: "All",
  temperatureUnit: "Kelvin",
};

export default function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const savedSettings = localStorage.getItem("moon-dashboard-settings");

    if (savedSettings) {
      try {
        setSettings({
          ...defaultSettings,
          ...JSON.parse(savedSettings),
        });
      } catch {
        setSettings(defaultSettings);
      }
    }
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setSettings((previous) => ({
      ...previous,
      [name]: value,
    }));

    setMessage("");
  };

  const handleSave = () => {
    localStorage.setItem(
      "moon-dashboard-settings",
      JSON.stringify(settings)
    );

    setMessage("Settings saved successfully.");
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.setItem(
      "moon-dashboard-settings",
      JSON.stringify(defaultSettings)
    );

    setMessage("Settings restored to defaults.");
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div>
          <p className="settings-eyebrow">PREFERENCES</p>
          <h1>Settings</h1>
          <p className="settings-subtitle">
            Manage your profile and experiment dashboard preferences.
          </p>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-section-heading">
          <div className="settings-icon">01</div>
          <div>
            <h2>Profile Settings</h2>
            <p>Customize your researcher profile.</p>
          </div>
        </div>

        <div className="settings-field">
          <label htmlFor="displayName">Display Name</label>
          <input
            id="displayName"
            name="displayName"
            type="text"
            value={settings.displayName}
            onChange={handleChange}
            placeholder="Enter display name"
          />
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-section-heading">
          <div className="settings-icon">02</div>
          <div>
            <h2>Dashboard Preferences</h2>
            <p>Choose which dashboard page you prefer to open.</p>
          </div>
        </div>

        <div className="settings-field">
          <label htmlFor="defaultPage">Default Page</label>
          <select
            id="defaultPage"
            name="defaultPage"
            value={settings.defaultPage}
            onChange={handleChange}
          >
            <option value="Overview">Overview</option>
            <option value="Explorer">Experiment Explorer</option>
            <option value="Comparison">Comparison</option>
            <option value="AI Insights">AI Insights</option>
            <option value="Data Quality">Data Sources</option>
            <option value="Computer Vision">Computer Vision</option>
          </select>
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-section-heading">
          <div className="settings-icon">03</div>
          <div>
            <h2>Experiment Preferences</h2>
            <p>Set your preferred experiment filters and temperature unit.</p>
          </div>
        </div>

        <div className="settings-fields-grid">
          <div className="settings-field">
            <label htmlFor="defaultStatus">Default Status Filter</label>
            <select
              id="defaultStatus"
              name="defaultStatus"
              value={settings.defaultStatus}
              onChange={handleChange}
            >
              <option value="All">All Experiments</option>
              <option value="Validated">Validated</option>
              <option value="Under Review">Under Review</option>
            </select>
          </div>

          <div className="settings-field">
            <label htmlFor="temperatureUnit">Temperature Unit</label>
            <select
              id="temperatureUnit"
              name="temperatureUnit"
              value={settings.temperatureUnit}
              onChange={handleChange}
            >
              <option value="Kelvin">Kelvin (K)</option>
              <option value="Celsius">Celsius (°C)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="settings-footer">
        <div className="settings-feedback" role="status">
          {message}
        </div>

        <div className="settings-actions">
          <button
            className="settings-reset-btn"
            type="button"
            onClick={handleReset}
          >
            Reset Defaults
          </button>

          <button
            className="settings-save-btn"
            type="button"
            onClick={handleSave}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}