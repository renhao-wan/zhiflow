import { ApiClientError } from "./api";

export function getQaErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 404) {
      return "问答服务还没有响应。请重启后端服务。";
    }

    if (error.errorCode === "TRANSCRIPT_EMPTY") {
      return "当前记录没有可用于问答的内容文本。可以先生成转写稿，再继续提问。";
    }

    if (error.errorCode === "RATE_LIMITED") {
      return error.message;
    }

    if (error.errorCode === "NETWORK_ERROR") {
      return error.message;
    }

    if (error.errorCode === "TIMEOUT") {
      return "问答请求超时。远程服务响应慢或后端忙时可能发生，可以稍后重试。";
    }

    if (error.status === 422) {
      return "问答请求参数和后端版本不一致。请刷新页面并重启后端后再试。";
    }

    return error.message;
  }

  return error instanceof Error ? error.message : "问答生成失败，请稍后重试。";
}
