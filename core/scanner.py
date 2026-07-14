import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urljoin

DEFAULT_TIMEOUT = 10


async def fetch(session, url):
    try:
        async with session.get(url, timeout=DEFAULT_TIMEOUT) as resp:
            text = await resp.text(errors="ignore")
            return {
                "url": str(resp.url),
                "status": resp.status,
                "length": len(text),
            }
    except asyncio.TimeoutError:
        return {"url": url, "status": "timeout", "length": 0}
    except Exception as e:
        return {"url": url, "status": "error", "length": 0, "error": str(e)}


async def scan_single_base(
    base_url,
    wordlist_path,
    extensions=None,
    match_status=None,
    concurrency=50,
):
    """
    Native directory scanner for a single base URL using aiohttp.
    """
    if extensions is None:
        extensions = [""]
    if match_status is None:
        match_status = {200, 204, 301, 302, 307, 401, 403}

    wordlist = Path(wordlist_path)
    if not wordlist.is_file():
        raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")

    words = [w.strip() for w in wordlist.read_text().splitlines() if w.strip()]

    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(
        total=None,
        sock_connect=DEFAULT_TIMEOUT,
        sock_read=DEFAULT_TIMEOUT,
    )

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        sem = asyncio.Semaphore(concurrency)
        tasks = []

        async def worker(full_url):
            async with sem:
                result = await fetch(session, full_url)
                if isinstance(result["status"], int) and result["status"] in match_status:
                    print(f"[+] {result['status']:3} | {result['length']:6} | {result['url']}")
                return result

        for word in words:
            for ext in extensions:
                path = f"/{word}{ext}"
                full_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
                tasks.append(asyncio.create_task(worker(full_url)))

        results = await asyncio.gather(*tasks)
        return results
