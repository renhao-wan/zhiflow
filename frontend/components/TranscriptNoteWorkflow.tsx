"use client";

import { FileDown, Loader2 } from "lucide-react";
import { CandidateQueue } from "./CandidateQueue";
import { DraftHighlightsSection } from "./DraftHighlightsSection";
import type { DraftEditStatus } from "@/lib/transcript-workbench";
import type { SummaryHighlight } from "@/lib/types";

interface TranscriptNoteWorkflowProps {
  candidateHighlights: SummaryHighlight[];
  draftEditStatuses: Record<string, DraftEditStatus>;
  draftEditValues: Record<string, string>;
  draftErrorMessage: string | null;
  draftHighlights: SummaryHighlight[];
  draftMessage: string | null;
  isExportingNote: boolean;
  isSavingDraft: boolean;
  recentlyAddedHighlightId: string | null;
  savedHighlightIdentities: Set<string>;
  sourceUrl?: string | null;
  textSourceType?: string | null;
  onAddCandidate: (highlight: SummaryHighlight) => void;
  onDraftTextBlur: (highlightId: string) => void;
  onDraftTextChange: (highlightId: string, text: string) => void;
  onExportNote: () => void;
  onRemoveHighlight: (highlightId: string) => void;
}

export function TranscriptNoteWorkflow({
  candidateHighlights,
  draftEditStatuses,
  draftEditValues,
  draftErrorMessage,
  draftHighlights,
  draftMessage,
  isExportingNote,
  isSavingDraft,
  recentlyAddedHighlightId,
  savedHighlightIdentities,
  sourceUrl,
  textSourceType,
  onAddCandidate,
  onDraftTextBlur,
  onDraftTextChange,
  onExportNote,
  onRemoveHighlight
}: TranscriptNoteWorkflowProps) {
  return (
    <aside className="min-w-0 border-2 border-[var(--line-ink)] bg-[var(--paper-raised)] shadow-[3px_3px_0_0_var(--accent)] lg:sticky lg:top-[9rem] lg:flex lg:max-h-[calc(100dvh-10rem)] lg:flex-col lg:overflow-hidden">
      <header className="flex shrink-0 items-start justify-between gap-3 border-b border-[var(--line-strong)] p-3">
        <div>
          <h3 className="font-editorial text-base font-bold text-[var(--ink)]">摘录草稿</h3>
          <p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">
            已收集 {draftHighlights.length} 条，手动与 AI 摘录统一在这里编辑。
          </p>
        </div>
        <button
          className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 bg-[var(--accent)] px-3 text-xs font-semibold text-[var(--paper-raised)] transition-colors hover:bg-[var(--accent-deep)] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isExportingNote || !sourceUrl}
          type="button"
          onClick={onExportNote}
        >
          {isExportingNote ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <FileDown className="h-4 w-4" aria-hidden="true" />
          )}
          {isExportingNote ? "导出中" : "导出知识草稿"}
        </button>
      </header>

      <div className="min-h-0 divide-y divide-[var(--line-strong)] lg:flex-1 lg:overflow-y-auto">
        <DraftHighlightsSection
          draftErrorMessage={draftErrorMessage}
          draftHighlights={draftHighlights}
          draftMessage={draftMessage}
          editStatuses={draftEditStatuses}
          editValues={draftEditValues}
          isSavingDraft={isSavingDraft}
          recentlyAddedHighlightId={recentlyAddedHighlightId}
          onFinishEditing={onDraftTextBlur}
          onRemove={onRemoveHighlight}
          onTextChange={onDraftTextChange}
        />
        <CandidateQueue
          candidateHighlights={candidateHighlights}
          isSavingDraft={isSavingDraft}
          savedHighlightIdentities={savedHighlightIdentities}
          textSourceType={textSourceType}
          onAddCandidate={onAddCandidate}
        />
      </div>
    </aside>
  );
}
