/**
 * 跨平台运行 lib/*.test.ts：在 Windows 上 shell 不会展开 glob，
 * 这里用 Node 显式枚举测试文件后逐个传给测试 runner。
 */
import { readdirSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const libDir = resolve("lib");
const testFiles = readdirSync(libDir)
  .filter((name) => name.endsWith(".test.ts"))
  .map((name) => resolve(libDir, name));

if (testFiles.length === 0) {
  console.error("No lib/*.test.ts files found in " + libDir);
  process.exit(1);
}

const result = spawnSync(
  process.execPath,
  ["--import", "tsx", "--test", ...testFiles],
  { stdio: "inherit" }
);

process.exit(result.status ?? 1);
