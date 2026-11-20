import type { Measurement } from '../../types/schemas'

type Row = {
  id: string
  fuel: string
  pressure: number
  temperature: number
  source: string
  temps: number[] | null
  oxygen: number | null
  rate: number | null
}

const ROWS: Row[] = [
  { id: 'MOCK-EX-001', fuel: 'Methane', pressure: 0.1, temperature: 300, source: 'SRC-MOCK-001', temps: [300, 520, 740, 890, 820, 700], oxygen: 21.0, rate: 0.31 },
  { id: 'MOCK-EX-002', fuel: 'Ethanol', pressure: 0.2, temperature: 400, source: 'SRC-MOCK-002', temps: [310, 480, 680, 820, 780, 650], oxygen: 21.0, rate: 0.22 },
  { id: 'MOCK-EX-003', fuel: 'Propane', pressure: 0.1, temperature: 500, source: 'SRC-MOCK-003', temps: [290, 450, 710, 850, 790, 670], oxygen: 21.0, rate: 0.14 },
  // MOCK-EX-004 intentionally has no measurements (empty-state test).
]

const ILLUSTRATIVE_NOTE = 'ILLUSTRATIVE mock value — not a NASA measurement.'

export const mockMeasurements: Measurement[] = ROWS.flatMap((row) => {
  const conditions = {
    fuel: row.fuel,
    pressure: row.pressure,
    temperature: row.temperature,
    flow_velocity: null,
  }
  const base = {
    experiment_id: row.id,
    conditions,
    source_id: row.source,
    measurement_status: 'illustrative',
  }
  const n = row.id.slice(-3)
  const list: Measurement[] = []

  ;(row.temps ?? []).forEach((value, time) => {
    list.push({
      ...base,
      measurement_id: `MOCK-MEAS-${n}-T${time}`,
      variable: 'flame_temperature',
      value,
      unit: 'K',
      timestamp: time,
      notes: [ILLUSTRATIVE_NOTE],
    })
  })
  if (row.oxygen != null) {
    list.push({
      ...base,
      measurement_id: `MOCK-MEAS-${n}-O2`,
      variable: 'oxygen_concentration',
      value: row.oxygen,
      unit: 'percent',
      timestamp: null,
      notes: [ILLUSTRATIVE_NOTE],
    })
  }
  if (row.rate != null) {
    list.push({
      ...base,
      measurement_id: `MOCK-MEAS-${n}-R`,
      variable: 'combustion_rate',
      value: row.rate,
      unit: 'mock_unit/s',
      timestamp: null,
      notes: [ILLUSTRATIVE_NOTE, 'Unit is a placeholder; no real unit is implied.'],
    })
  }
  return list
})
