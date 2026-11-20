import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Search,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  SlidersHorizontal,
} from 'lucide-react'
import StatusBadge from '../components/ui/StatusBadge'
import MockNotice from '../components/ui/MockNotice'
import { formatRange } from '../utils/format'
import fireImage from '../assets/fire.png'
import '../styles/Explorer.css'

const TEMP_MIN = 300
const TEMP_MAX = 1200
const PRESSURE_MIN = 0.1
const PRESSURE_MAX = 1

const STANDARD_FUELS = ['Methane', 'Ethanol', 'Propane']

const FUEL_FILTER_OPTIONS = [
  { value: 'All', label: 'All' },
  ...STANDARD_FUELS.map((fuel) => ({
    value: fuel,
    label: fuel,
  })),
  { value: 'Other', label: 'Other' },
]

function normalizeFuel(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function isOtherFuel(value) {
  const normalized = normalizeFuel(value).toLowerCase()

  return (
    normalized !== '' &&
    !STANDARD_FUELS.some(
      (fuel) => fuel.toLowerCase() === normalized,
    )
  )
}

function matchesFuelCategory(actualFuel, selectedFuel) {
  if (selectedFuel === 'All') return true

  if (selectedFuel === 'Other') {
    return isOtherFuel(actualFuel)
  }

  return (
    normalizeFuel(actualFuel).toLowerCase() ===
    selectedFuel.toLowerCase()
  )
}

/* Reusable custom dropdown */
function CustomDropdown({
  label,
  value,
  displayValue,
  options,
  onChange,
}) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  useEffect(() => {
    function handleOutsideClick(event) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target)
      ) {
        setIsOpen(false)
      }
    }

    function handleEscape(event) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleOutsideClick)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener(
        'mousedown',
        handleOutsideClick,
      )
      document.removeEventListener(
        'keydown',
        handleEscape,
      )
    }
  }, [])

  return (
    <div
      ref={dropdownRef}
      className={`explorer-custom-dropdown ${
        isOpen ? 'is-open' : ''
      }`}
    >
      <span className="explorer-custom-label">{label}</span>

      <button
        type="button"
        className="explorer-custom-trigger"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
      >
        <span className="explorer-custom-value">
          {displayValue ??
            options.find((option) => option.value === value)
              ?.label ??
            value}
        </span>

        <ChevronDown
          size={16}
          className={`explorer-custom-chevron ${
            isOpen ? 'rotated' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div
          className="explorer-custom-menu"
          role="listbox"
          aria-label={label}
        >
          {options.map((option) => {
            const selected = option.value === value

            return (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={selected}
                className={`explorer-custom-option ${
                  selected ? 'selected' : ''
                }`}
                onClick={() => {
                  onChange(option.value)
                  setIsOpen(false)
                }}
              >
                <span>{option.label}</span>

                {selected && (
                  <span className="explorer-option-check">
                    ✓
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Explorer({
  experiments = [],
  globalSearch = '',
  setPage,
  setSelected,
}) {
  const [query, setQuery] = useState('')
  const [fuel, setFuel] = useState('All')
  const [status, setStatus] = useState('All')
  const [temperature, setTemperature] = useState(TEMP_MAX)
  const [pressure, setPressure] = useState(PRESSURE_MAX)
  const [checkedFuels, setCheckedFuels] = useState([])

  const statusOptions = useMemo(
    () => [
      ...new Set(
        experiments
          .map((item) => item.status)
          .filter(Boolean),
      ),
    ],
    [experiments],
  )

  const temperatureOptions = [
    { value: 'All', label: 'All' },
    { value: '500', label: 'Up to 500 K' },
    { value: '700', label: 'Up to 700 K' },
    { value: '900', label: 'Up to 900 K' },
  ]

  const pressureOptions = [
    { value: 'All', label: 'All' },
    { value: '0.1', label: 'Up to 0.1 atm' },
    { value: '0.2', label: 'Up to 0.2 atm' },
    { value: '0.5', label: 'Up to 0.5 atm' },
  ]

  const filtered = useMemo(() => {
    const searchTerm = [globalSearch, query]
      .filter(Boolean)
      .join(' ')
      .trim()
      .toLowerCase()

    return experiments.filter((item) => {
      const searchable = [
        item.id,
        item.title,
        item.fuel,
        item.category,
        item.platform,
        item.source,
        item.summary,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      const matchesSearch =
        !searchTerm ||
        searchTerm
          .split(/\s+/)
          .every((word) => searchable.includes(word))

      const matchesDropdownFuel = matchesFuelCategory(
        item.fuel,
        fuel,
      )

      const matchesCheckboxFuel =
        checkedFuels.length === 0 ||
        checkedFuels.some((selectedFuel) =>
          matchesFuelCategory(item.fuel, selectedFuel),
        )

      const matchesFuel =
        matchesDropdownFuel && matchesCheckboxFuel

      const matchesStatus =
        status === 'All' || item.status === status

      const itemMinTemperature = Number(
        item.temperatureMin ?? TEMP_MIN,
      )

      const itemMaxTemperature = Number(
        item.temperatureMax ?? TEMP_MAX,
      )

      const matchesTemperature =
        itemMinTemperature <= temperature &&
        itemMaxTemperature >= TEMP_MIN

      const matchesPressure =
        item.pressure == null ||
        Number(item.pressure) <= pressure

      return (
        matchesSearch &&
        matchesFuel &&
        matchesStatus &&
        matchesTemperature &&
        matchesPressure
      )
    })
  }, [
    experiments,
    globalSearch,
    query,
    fuel,
    status,
    temperature,
    pressure,
    checkedFuels,
  ])

  function resetFilters() {
    setQuery('')
    setFuel('All')
    setStatus('All')
    setTemperature(TEMP_MAX)
    setPressure(PRESSURE_MAX)
    setCheckedFuels([])
  }

  function toggleFuel(value) {
    setCheckedFuels((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    )
  }

  function openDetails(experiment) {
    setSelected?.(experiment)
    setPage?.('Details')
  }

  return (
    <div className="page explorer-page">
      <div className="page-heading explorer-heading">
        <div>
          <h1>Experiment Explorer</h1>
          <p>
            Browse and filter microgravity combustion experiments.
          </p>
        </div>

        <span className="count-pill">
          {filtered.length} experiments
        </span>
      </div>

      <div className="explorer-toolbar">
        <label
          className="explorer-search"
          aria-label="Search experiments"
        >
          <Search size={17} />

          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by ID, title or keyword..."
          />
        </label>

        <CustomDropdown
          label="Fuel Type"
          value={fuel}
          options={FUEL_FILTER_OPTIONS}
          onChange={setFuel}
        />

        <CustomDropdown
          label="Temperature Range"
          value={
            temperature === TEMP_MAX
              ? 'All'
              : String(temperature)
          }
          displayValue={
            temperature === TEMP_MAX
              ? 'All'
              : `Up to ${temperature} K`
          }
          options={[
            ...temperatureOptions,
            ...(temperature !== TEMP_MAX &&
            ![500, 700, 900].includes(temperature)
              ? [
                  {
                    value: String(temperature),
                    label: `Up to ${temperature} K`,
                  },
                ]
              : []),
          ]}
          onChange={(value) =>
            setTemperature(
              value === 'All' ? TEMP_MAX : Number(value),
            )
          }
        />

        <CustomDropdown
          label="Pressure Range"
          value={
            pressure === PRESSURE_MAX
              ? 'All'
              : String(pressure)
          }
          displayValue={
            pressure === PRESSURE_MAX
              ? 'All'
              : `Up to ${pressure} atm`
          }
          options={[
            ...pressureOptions,
            ...(pressure !== PRESSURE_MAX &&
            ![0.1, 0.2, 0.5].includes(pressure)
              ? [
                  {
                    value: String(pressure),
                    label: `Up to ${pressure} atm`,
                  },
                ]
              : []),
          ]}
          onChange={(value) =>
            setPressure(
              value === 'All'
                ? PRESSURE_MAX
                : Number(value),
            )
          }
        />

        <CustomDropdown
          label="Status"
          value={status}
          options={[
            { value: 'All', label: 'All' },
            ...statusOptions.map((item) => ({
              value: item,
              label: item,
            })),
          ]}
          onChange={setStatus}
        />

        <button
          className="explorer-reset"
          type="button"
          onClick={resetFilters}
        >
          <RotateCcw size={14} />
          Reset
        </button>
      </div>

      <div className="explorer-layout explorer-reference-layout">
        <section
          className="results-column"
          aria-label="Experiment results"
        >
          <div className="experiment-list explorer-cards">
            {filtered.map((experiment) => (
              <button
                className="experiment-row explorer-card"
                key={experiment.id}
                type="button"
                onClick={() => openDetails(experiment)}
                aria-label={`View details for ${experiment.id} ${experiment.title}`}
              >
                <img
                  className="experiment-thumb explorer-thumb-image"
                  src={fireImage}
                  alt="Fire combustion experiment"
                />

                <div className="experiment-copy explorer-card-copy">
                  <div className="explorer-card-title-line">
                    <div className="explorer-title-text">
                      <span className="experiment-id">
                        {experiment.id}
                      </span>

                      <strong>{experiment.title}</strong>
                    </div>

                    <StatusBadge
                      status={experiment.status}
                      statusKey={experiment.statusKey}
                    />
                  </div>

                  <div className="explorer-tags">
                    {[
                      experiment.fuel,
                      experiment.platform,
                      experiment.category,
                    ]
                      .filter(Boolean)
                      .map((tag, index) => (
                        <span
                          key={`${experiment.id}-${tag}-${index}`}
                        >
                          {tag}
                        </span>
                      ))}
                  </div>

                  <div className="explorer-meta">
                    <span>
                      T: {formatRange(experiment.temperatureMin, experiment.temperatureMax, 'K')}
                    </span>

                    <span>
                      P: {formatRange(experiment.pressure, experiment.pressureMax, 'atm')}
                    </span>

                    <span>
                      Source: {experiment.source || 'Not specified'}
                    </span>
                  </div>
                </div>

                <ChevronRight
                  className="explorer-card-arrow"
                  size={19}
                />
              </button>
            ))}

            {filtered.length === 0 && (
              <div className="explorer-empty">
                <Search size={25} />

                <strong>No experiments found</strong>

                <p>
                  Try changing your search terms or clearing one
                  or more filters.
                </p>

                <button
                  className="secondary-button"
                  type="button"
                  onClick={resetFilters}
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>

          <MockNotice />
        </section>

        <aside className="panel filters-panel explorer-condition-panel">
          <div className="panel-title">
            <SlidersHorizontal size={17} />
            <h3>Filter by Conditions</h3>
          </div>

          <div className="condition-control">
            <div className="condition-label">
              <span>Temperature (K)</span>
              <strong>{temperature}</strong>
            </div>

            <input
              aria-label="Maximum temperature in kelvin"
              type="range"
              min={TEMP_MIN}
              max={TEMP_MAX}
              step="50"
              value={temperature}
              onChange={(event) =>
                setTemperature(Number(event.target.value))
              }
            />

            <div className="range-endpoints">
              <span>{TEMP_MIN}</span>
              <span>{TEMP_MAX}</span>
            </div>
          </div>

          <div className="condition-control">
            <div className="condition-label">
              <span>Pressure (atm)</span>
              <strong>{pressure.toFixed(1)}</strong>
            </div>

            <input
              aria-label="Maximum pressure in atmospheres"
              type="range"
              min={PRESSURE_MIN}
              max={PRESSURE_MAX}
              step="0.1"
              value={pressure}
              onChange={(event) =>
                setPressure(Number(event.target.value))
              }
            />

            <div className="range-endpoints">
              <span>{PRESSURE_MIN.toFixed(1)}</span>
              <span>{PRESSURE_MAX.toFixed(1)}</span>
            </div>
          </div>

          <div className="fuel-check-section">
            <span className="fuel-check-heading">Fuel Type</span>

            <div className="fuel-check-grid">
              {FUEL_FILTER_OPTIONS.filter(
                (option) => option.value !== 'All',
              ).map((option) => (
                <label
                  key={option.value}
                  className="fuel-check-option"
                >
                  <input
                    type="checkbox"
                    checked={checkedFuels.includes(option.value)}
                    onChange={() => toggleFuel(option.value)}
                  />

                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            className="primary-button explorer-apply"
            type="button"
          >
            Apply Filters
          </button>
        </aside>
      </div>
    </div>
  )
}