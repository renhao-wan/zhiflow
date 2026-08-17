"use client";

import { Plus } from "lucide-react";

export interface SelectionData {
  charCount: number;
  left: number;
  top: number;
}

interface SelectionToolbarProps {
  selection: SelectionData | null;
  isAdding: boolean;
  onAdd: () => void;
}

export function SelectionToolbar({ selection, isAdding, onAdd }: SelectionToolbarProps) {
  if (!selection) {
    return null;
  }

  return (
    <div
      className="fixed z-50 flex -translate-x-1/2 items-center gap-2 rounded-[2px] border border-[var(--line-ink)] bg-[var(--paper-raised)]/95 px-3 py-2 text-xs font-medium text-[var(--ink-soft)] shadow-[0_16px_40px_rgba(33,29,23,0.16)] backdrop-blur"
      style={{ left: selection.left, top: selection.top }}
      onMouseDown={(event) => event.preventDefault()}
    >
      <span className="mono tabular-nums text-[var(--accent)]">
        已选 {selection.charCount} 字
      </span>
      <button
        className="inline-flex h-8 items-center justify-center gap-1.5 rounded-[2px] bg-[var(--ink)] px-3 text-xs font-semibold text-[var(--paper)] transition-colors hover:bg-[var(--accent-deep)] disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isAdding}
        type="button"
        onClick={onAdd}
      >
        <Plus className="h-3.5 w-3.5" />
        加入摘录
      </button>
    </div>
  );
}
