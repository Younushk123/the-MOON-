import type { Experiment } from '../../types/schemas'

const MOCK_LIMITATION =
  'MOCK RECORD: fictional interface placeholder. Not a NASA record and not a verified finding.'

export const mockExperiments: Experiment[] = [
  {
    experiment_id: 'MOCK-EX-001',
    name: 'Methane Combustion in Microgravity',
    investigation: 'Combustion',
    program: 'MOCK DATA (not a NASA program)',
    description:
      'Illustrative methane combustion record used to test the experiment details and comparison views.',
    platform: 'Mock platform (not a real mission)',
    source_ids: ['SRC-MOCK-001'],
    data_status: 'mock',
    available_measurements: ['flame_temperature', 'oxygen_concentration', 'combustion_rate'],
    limitations: [MOCK_LIMITATION],
    last_updated: '2026-11-14',
  },
  {
    experiment_id: 'MOCK-EX-002',
    name: 'Fuel Droplet Ignition Study',
    investigation: 'Ignition',
    program: 'MOCK DATA (not a NASA program)',
    description:
      'Illustrative droplet ignition record. Values are placeholders and are not scientific conclusions.',
    platform: 'Mock platform (not a real mission)',
    source_ids: ['SRC-MOCK-002'],
    data_status: 'mock',
    available_measurements: ['flame_temperature', 'oxygen_concentration', 'combustion_rate'],
    limitations: [MOCK_LIMITATION],
    last_updated: '2026-11-14',
  },
  {
    experiment_id: 'MOCK-EX-003',
    name: 'Flame Spread Analysis',
    investigation: 'Flame Spread',
    program: 'MOCK DATA (not a NASA program)',
    description:
      'Illustrative flame spread record for testing charts, filtering and comparison interactions.',
    platform: 'Mock platform (not a real mission)',
    source_ids: ['SRC-MOCK-003'],
    data_status: 'mock',
    available_measurements: ['flame_temperature', 'oxygen_concentration', 'combustion_rate'],
    limitations: [MOCK_LIMITATION],
    last_updated: '2026-11-14',
  },
  {
    experiment_id: 'MOCK-EX-004',
    name: 'Solid Fuel Extinction Test',
    investigation: 'Extinction',
    program: 'MOCK DATA (not a NASA program)',
    description:
      'Example record with no measurements, used to test missing-data and empty states in the interface.',
    platform: 'Mock platform (not a real mission)',
    source_ids: ['SRC-MOCK-001'],
    data_status: 'mock',
    available_measurements: [],
    limitations: [MOCK_LIMITATION, 'No measurement records are available for this mock experiment.'],
    last_updated: '2026-11-14',
  },
]
