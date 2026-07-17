"""Crawler base framework - rate limiting, retry, HTTP client"""
import time
import random
import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Rotating User-Agent pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


class RateLimiter:
    """Rate limiter with jitter to avoid being blocked"""

    def __init__(self, min_interval: float = 1.5, jitter: float = 0.5):
        self.min_interval = min_interval
        self.jitter = jitter
        self._last_request = 0.0

    def wait(self):
        """Block until next request is allowed"""
        now = time.time()
        elapsed = now - self._last_request
        delay = self.min_interval + random.uniform(0, self.jitter)
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request = time.time()


class CrawlerClient:
    """HTTP client with rate limiting, retry, and UA rotation"""

    def __init__(
        self,
        base_delay: float = 2.0,
        jitter: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.rate_limiter = RateLimiter(min_interval=base_delay, jitter=jitter)
        self.timeout = timeout

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, headers: Optional[dict] = None, **kwargs) -> requests.Response:
        """Rate-limited GET request"""
        self.rate_limiter.wait()
        req_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        }
        if headers:
            req_headers.update(headers)

        logger.info(f"GET {url}")
        resp = self.session.get(url, headers=req_headers, timeout=self.timeout, **kwargs)
        resp.raise_for_status()
        return resp

    def close(self):
        self.session.close()
