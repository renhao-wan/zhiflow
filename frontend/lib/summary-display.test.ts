import assert from "node:assert/strict";
import test from "node:test";
import { getTopicIdentity, getTopicTags } from "./summary-display";
import type { VideoSummary } from "./types";

function makeSummary(overrides: Partial<VideoSummary>): VideoSummary {
  return {
    tldr: "",
    title: "",
    key_points: [],
    structured_analysis_markdown: "",
    ...overrides
  } as VideoSummary;
}

test("getTopicIdentity 归一化空白、连字符与全角字符", () => {
  assert.equal(getTopicIdentity("AI·智能  助手"), "ai智能助手");
  assert.equal(getTopicIdentity("本地-知识/库"), "本地知识库");
});

test("getTopicTags 去重且合并 topics 与 content_keywords", () => {
  const summary = makeSummary({
    topics: ["AI 应用", "本地知识库", "AI 应用"],
    content_keywords: ["知识管理", "AI应用"]
  });
  // "AI 应用" 与 "AI应用" 近重复，只保留一个
  const tags = getTopicTags(summary);
  assert.equal(tags.includes("AI 应用"), true);
  assert.equal(tags.includes("AI应用"), false);
  assert.equal(tags.includes("本地知识库"), true);
  assert.equal(tags.includes("知识管理"), true);
});

test("getTopicTags 最多返回 6 个", () => {
  const manyTopics = Array.from({ length: 10 }, (_, index) => `主题 ${index + 1}`);
  const tags = getTopicTags(makeSummary({ topics: manyTopics }));
  assert.equal(tags.length, 6);
});

test("getTopicTags 过滤空串", () => {
  const tags = getTopicTags(
    makeSummary({ topics: ["", "   ", "有效主题", "  "], content_keywords: [] })
  );
  assert.deepEqual(tags, ["有效主题"]);
});
