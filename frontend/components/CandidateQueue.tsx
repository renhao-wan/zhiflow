"use client";

import { CheckCircle2, Plus } from "lucide-react";
import { useState } from "react";
import { IconActionButton } from "./IconActionButton";
import {
  getHighlightIdentity,
  getHighlightSourceLabel,
  normalizeCandidateHighlight
} from "@/lib/transcript-workbench";
import type { SummaryHighlight } from "@/lib/types";

interface CandidateQueueProps {
  candidateHighlights: SummaryHighlight[];
  isSavingDraft: boolean;
  savedHighlightIdentities: Set<string>;
  textSourceType?: string | null;
  onAddCandidate: (highlight: SummaryHighlight) => void;
}

export function CandidateQueue({
  candidateHighlights,
  isSavingDraft,
  savedHighlightIdentities,
  textSourceType,
  onAddCandidate
}: CandidateQueueProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <section>
      <button
        aria-expanded={isOpen}
        className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left transition-colors hover:bg-[var(--paper)]"
        type="button"
        onClick={() => setIsOpen((current) => !current)}
      >
        <span>
          <span className="font-editorial text-base font-bold text-[var(--ink)]">AI 候选</span>
          <span className="ml-2 text-xs font-semibold tabular-nums text-[var(--accent)]">
            {candidateHighlights.length} 条
          </span>
        </span>
        <span className="text-xs font-medium text-[var(--muted)]">
          {isOpen ? "收起" : "展开"}
        </span>
      </button>

      {isOpen ? (
        <div className="grid gap-2 px-3 pb-3">
          {candidateHighlights.length > 0 ? (
            candidateHighlights.map((highlight) => {
              const normalizedHighlight = normalizeCandidateHighlight(
                highlight,
                textSourceType
              );
              const isSaved = savedHighlightIdentities.has(
                getHighlightIdentity(normalizedHighlight)
              );

              return (
                <div
                  className="border border-[var(--line-strong)] bg-[var(--paper)] px-3 py-3"
                  key={`${highlight.id}-${highlight.text}`}
                >
                  <div className="mb-2 flex items-center justify-between gap-2 text-[11px] text-[var(--muted)]">
                    <span>{getHighlightSourceLabel(highlight)}</span>
                    <IconActionButton
                      disabled={isSavingDraft || isSaved}
                      icon={isSaved ? CheckCircle2 : Plus}
                      label={isSaved ? "已加入摘录草稿" : "加入摘录草稿"}
                      tone={isSaved ? "accent" : "default"}
                      onClick={() => onAddCandidate(highlight)}
                    />
                  </div>
                  <p className="font-editorial text-sm leading-6 text-[var(--ink-soft)]">
                    {highlight.text}
                  </p>
                </div>
              );
            })
          ) : (
            <div className="border border-dashed border-[var(--line-strong)] bg-[var(--paper)] px-3 py-3 text-xs leading-5 text-[var(--muted)]">
              生成总结后，这里会显示候选摘录。
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
