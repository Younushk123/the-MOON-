import { ArrowUpRight } from 'lucide-react'
export default function StatCard({ icon: Icon, label, value, note }) { return <div className="stat-card"><div className="stat-icon"><Icon size={18}/></div><div className="stat-label">{label}</div><strong>{value}</strong><small><ArrowUpRight size={12}/>{note}</small></div> }
