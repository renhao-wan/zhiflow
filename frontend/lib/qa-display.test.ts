import assert from "node:assert/strict";
import test from "node:test";
import { ApiClientError } from "./api";
import { getQaErrorMessage } from "./qa-display";

test("getQaErrorMessage 处理 404", () => {
  const message = getQaErrorMessage(new ApiClientError("not found", 404));
  assert.match(message, /重启后端服务/);
});

test("getQaErrorMessage 处理空内容文本", () => {
  const message = getQaErrorMessage(
    new ApiClientError("empty", 400, "TRANSCRIPT_EMPTY")
  );
  assert.match(message, /可以先生成转写稿/);
});

test("getQaErrorMessage 处理限流与网络错误时透传 message", () => {
  assert.equal(
    getQaErrorMessage(new ApiClientError("slow down", 429, "RATE_LIMITED")),
    "slow down"
  );
  assert.equal(
    getQaErrorMessage(new ApiClientError("unreachable", 0, "NETWORK_ERROR")),
    "unreachable"
  );
});

test("getQaErrorMessage 处理超时", () => {
  const message = getQaErrorMessage(new ApiClientError("timeout", 0, "TIMEOUT"));
  assert.match(message, /请求超时/);
});

test("getQaErrorMessage 处理 422", () => {
  const message = getQaErrorMessage(new ApiClientError("bad request", 422));
  assert.match(message, /参数和后端版本不一致/);
});

test("getQaErrorMessage 兜底普通 Error 与未知值", () => {
  assert.equal(getQaErrorMessage(new Error("boom")), "boom");
  assert.equal(getQaErrorMessage("oops"), "问答生成失败，请稍后重试。");
});
