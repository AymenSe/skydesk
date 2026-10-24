"""Exit 0 if the worker's heartbeat is fresh, 1 otherwise. Used by the Docker healthcheck."""
import sys

import redis

from skydesk.core.config import get_settings
from skydesk.core.queue import HEARTBEAT_KEY


def main() -> int:
    r = redis.Redis.from_url(get_settings().redis_url)
    return 0 if r.exists(HEARTBEAT_KEY) else 1


if __name__ == "__main__":
    sys.exit(main())