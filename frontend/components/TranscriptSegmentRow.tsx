"use client";

import { formatTimestamp } from "@/lib/transcript-workbench";
import type { TranscriptSegment } from "@/lib/types";

interface TranscriptSegmentRowProps {
  segment: TranscriptSegment;
}

export function TranscriptSegmentRow({ segment }: TranscriptSegmentRowProps) {
  return (
    <div className="grid gap-3 border-b border-[var(--line-strong)] bg-[var(--paper-raised)] px-4 py-3 last:border-b-0 sm:grid-cols-[86px_minmax(0,1fr)]">
      <div className="select-none space-y-1">
        <div className="mono text-xs text-[var(--muted)]">
          {formatTimestamp(segment.start)}
        </div>
        {segment.speaker ? (
          <span className="inline-flex max-w-[76px] truncate rounded-[2px] bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-medium text-[var(--accent)]">
            {segment.speaker}
          </span>
        ) : null}
      </div>
      <p
        className="transcript-excerpt-text text-sm leading-6 text-[var(--ink-soft)]"
        data-excerpt-end={segment.end}
        data-excerpt-start={segment.start}
        data-transcript-excerpt="true"
      >
        {segment.text}
      </p>
    </div>
  );
}
