import type { VideoSummary } from "./types";

export function getTopicIdentity(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("zh-CN")
    .replace(/[\s·_\-/]+/gu, "");
}

export function getTopicTags(summary: VideoSummary): string[] {
  const seenTopicIdentities = new Set<string>();
  const topicTags: string[] = [];

  for (const topic of [...(summary.topics ?? []), ...(summary.content_keywords ?? [])]) {
    const normalizedTopic = topic.trim();
    const identity = getTopicIdentity(normalizedTopic);
    const isNearDuplicate = Array.from(seenTopicIdentities).some(
      (savedIdentity) =>
        Math.abs(savedIdentity.length - identity.length) <= 3 &&
        (savedIdentity.includes(identity) || identity.includes(savedIdentity))
    );
    if (
      !normalizedTopic ||
      !identity ||
      seenTopicIdentities.has(identity) ||
      isNearDuplicate
    ) {
      continue;
    }

    seenTopicIdentities.add(identity);
    topicTags.push(normalizedTopic);
    if (topicTags.length === 6) {
      break;
    }
  }

  return topicTags;
}
