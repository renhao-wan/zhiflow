"use client";

import { Pencil, Quote, Trash2 } from "lucide-react";
import { useEffect, useRef } from "react";
import { IconActionButton } from "./IconActionButton";
import { getHighlightSourceLabel, type DraftEditStatus } from "@/lib/transcript-workbench";
import type { SummaryHighlight } from "@/lib/types";

interface DraftHighlightCardProps {
  highlight: SummaryHighlight;
  editStatus?: DraftEditStatus;
  isEditing: boolean;
  isRecentlyAdded: boolean;
  isSavingDraft: boolean;
  visibleText: string;
  onStartEditing: (highlightId: string) => void;
  onFinishEditing: (highlightId: string) => void;
  onRemove: (highlightId: string) => void;
  onTextChange: (highlightId: string, text: string) => void;
}

function resizeDraftTextarea(element: HTMLTextAreaElement | null) {
  if (!element) {
    return;
  }

  element.style.height = "auto";
  element.style.height = `${element.scrollHeight}px`;
}

export function DraftHighlightCard({
  highlight,
  editStatus,
  isEditing,
  isRecentlyAdded,
  isSavingDraft,
  visibleText,
  onStartEditing,
  onFinishEditing,
  onRemove,
  onTextChange
}: DraftHighlightCardProps) {
  const cardRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isRecentlyAdded && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [isRecentlyAdded]);

  return (
    <div
      className={`scroll-mt-4 border bg-[var(--paper)] px-3 py-3 transition-colors ${
        isRecentlyAdded
          ? "border-2 border-[var(--accent)] bg-[var(--accent-soft)]/30 shadow-[2px_2px_0_0_var(--accent)]"
          : "border-[var(--line-strong)]"
      }`}
      key={highlight.id}
      ref={(element) => {
        cardRef.current = element;
      }}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5 text-[11px] text-[var(--muted)]">
          <Quote className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span className="truncate">{getHighlightSourceLabel(highlight)}</span>
          {isRecentlyAdded ? (
            <span className="shrink-0 font-semibold text-[var(--accent)]">刚加入</span>
          ) : null}
          {editStatus === "saving" ? (
            <span className="shrink-0 text-[var(--accent)]">保存中</span>
          ) : null}
          {editStatus === "saved" ? (
            <span className="shrink-0 text-[var(--success-ink)]">已保存</span>
          ) : null}
          {editStatus === "error" ? (
            <span className="shrink-0 text-[var(--error-ink)]">保存失败</span>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <IconActionButton
            disabled={isSavingDraft}
            icon={Pencil}
            label="编辑摘录"
            pressed={isEditing}
            onClick={() => onStartEditing(highlight.id)}
          />
          <IconActionButton
            disabled={isSavingDraft}
            icon={Trash2}
            label="移出摘录草稿"
            tone="danger"
            onClick={() => onRemove(highlight.id)}
          />
        </div>
      </div>

      {isEditing ? (
        <textarea
          aria-label="编辑摘录文字"
          autoFocus
          className="block min-h-[72px] w-full resize-none overflow-hidden border-2 border-[var(--accent)] bg-[var(--paper-raised)] px-2 py-1.5 text-sm leading-6 text-[var(--ink-soft)] outline-none shadow-[2px_2px_0_0_var(--accent-soft)]"
          ref={resizeDraftTextarea}
          rows={2}
          value={visibleText}
          onBlur={() => onFinishEditing(highlight.id)}
          onChange={(event) => {
            resizeDraftTextarea(event.currentTarget);
            onTextChange(highlight.id, event.currentTarget.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              onFinishEditing(highlight.id);
            }
          }}
        />
      ) : (
        <p className="font-editorial text-sm leading-6 text-[var(--ink-soft)]">{visibleText}</p>
      )}
    </div>
  );
}
