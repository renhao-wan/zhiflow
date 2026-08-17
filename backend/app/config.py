"""应用级配置常量。"""

import os

from app.http_utils import read_int_env

APP_VERSION = "0.1.0"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
PARSE_RATE_LIMIT_PER_HOUR = read_int_env("PARSE_RATE_LIMIT_PER_HOUR", 20)
SUMMARY_RATE_LIMIT_PER_HOUR = read_int_env("SUMMARY_RATE_LIMIT_PER_HOUR", 10)
QA_RATE_LIMIT_PER_HOUR = read_int_env("QA_RATE_LIMIT_PER_HOUR", 10)
TRANSCRIBE_RATE_LIMIT_PER_HOUR = read_int_env("TRANSCRIBE_RATE_LIMIT_PER_HOUR", 3)
IMAGE_PROXY_TIMEOUT_SECONDS = 15
IMAGE_PROXY_MAX_BYTES = 8 * 1024 * 1024
IMAGE_PROXY_ACCEPT_HEADER = (
    "image/avif,image/webp,image/apng,image/png,image/jpeg,"
    "image/*;q=0.8,*/*;q=0.5"
)
FRONTEND_ORIGINS = {
    FRONTEND_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}
