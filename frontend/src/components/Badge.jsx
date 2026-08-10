import { riscoClass, statusClass } from '../lib/format';

export function RiscoBadge({ value }) {
  return <span className={`hd-badge ${riscoClass(value)}`}>{value}</span>;
}

export function StatusBadge({ value }) {
  return <span className={`hd-badge ${statusClass(value)}`}>{value}</span>;
}
