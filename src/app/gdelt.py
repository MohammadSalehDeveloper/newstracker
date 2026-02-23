import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

logger = logging.getLogger(__name__)


def _requests_session_with_retries(retries: int = 3, backoff: float = 1.0):
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def fetch_gdelt(query: str, mode: str = "ArtList", maxrecords: int = 50, format_: str = "json", sort: str = "HybridRel"):
    """Query GDELT DOC API with retries and safe error handling.

    Returns parsed JSON on success or an empty dict on failure.
    """
    params = {
        "query": query,
        "mode": mode,
        "maxrecords": str(maxrecords),
        "format": format_,
        "sort": sort,
    }

    session = _requests_session_with_retries()
    try:
        r = session.get(GDELT_DOC_API, params=params, timeout=30)
        # If status is 429 (rate limit) or other 5xx, raise for visibility
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        logger.warning("GDELT HTTP error: %s - status=%s", e, getattr(e.response, "status_code", None))
    except requests.exceptions.SSLError as e:
        logger.warning("GDELT SSL error: %s", e)
    except requests.exceptions.ConnectionError as e:
        logger.warning("GDELT connection error: %s", e)
    except Exception as e:
        logger.exception("Unexpected error when fetching GDELT: %s", e)

    return {}