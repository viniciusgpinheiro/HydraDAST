import { riscoClass, statusClass } from '../data/mock';

export function RiscoBadge({ value }) {
  return <span className={`hd-badge ${riscoClass(value)}`}>{value}</span>;
}

export function StatusBadge({ value }) {
  return <span className={`hd-badge ${statusClass(value)}`}>{value}</span>;
}
