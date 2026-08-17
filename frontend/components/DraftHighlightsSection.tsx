"use client";

import { useState } from "react";
import { DraftHighlightCard } from "./DraftHighlightCard";
import type { DraftEditStatus } from "@/lib/transcript-workbench";
import type { SummaryHighlight } from "@/lib/types";

interface DraftHighlightsSectionProps {
  draftErrorMessage: string | null;
  draftHighlights: SummaryHighlight[];
  draftMessage: string | null;
  editStatuses: Record<string, DraftEditStatus | undefined>;
  editValues: Record<string, string>;
  isSavingDraft: boolean;
  recentlyAddedHighlightId: string | null;
  onFinishEditing: (highlightId: string) => void;
  onRemove: (highlightId: string) => void;
  onTextChange: (highlightId: string, text: string) => void;
}

export function DraftHighlightsSection({
  draftErrorMessage,
  draftHighlights,
  draftMessage,
  editStatuses,
  editValues,
  isSavingDraft,
  recentlyAddedHighlightId,
  onFinishEditing,
  onRemove,
  onTextChange
}: DraftHighlightsSectionProps) {
  const [editingHighlightId, setEditingHighlightId] = useState<string | null>(null);

  return (
    <section className="p-3">
      {draftMessage ? (
        <div className="mb-3 border-2 border-[var(--line-ink)] bg-[#e9f2ea] px-3 py-2 text-xs text-[#2f5d3a]">
          {draftMessage} 共 {draftHighlights.length} 条。
        </div>
      ) : null}
      {draftErrorMessage ? (
        <div className="mb-3 border-2 border-[var(--line-ink)] bg-[#f7ead9] px-3 py-2 text-xs text-[#7a4a1f]">
          {draftErrorMessage}
        </div>
      ) : null}

      {draftHighlights.length > 0 ? (
        <div className="grid gap-2">
          {draftHighlights.map((highlight) => (
            <DraftHighlightCard
              key={highlight.id}
              editStatus={editStatuses[highlight.id]}
              highlight={highlight}
              isEditing={editingHighlightId === highlight.id}
              isRecentlyAdded={recentlyAddedHighlightId === highlight.id}
              isSavingDraft={isSavingDraft}
              visibleText={editValues[highlight.id] ?? highlight.text}
              onFinishEditing={() => {
                onFinishEditing(highlight.id);
                setEditingHighlightId(null);
              }}
              onRemove={onRemove}
              onStartEditing={() => setEditingHighlightId(highlight.id)}
              onTextChange={onTextChange}
            />
          ))}
        </div>
      ) : (
        <div className="border border-dashed border-[var(--line-strong)] bg-[var(--paper)] px-3 py-3 text-xs leading-5 text-[var(--muted)]">
          在左侧原文中框选文字，再点击“加入摘录”。
        </div>
      )}
    </section>
  );
}
