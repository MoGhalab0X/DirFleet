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


def compute_baseline_length(results, match_status):
    lengths = [
        r["length"]
        for r in results
        if isinstance(r.get("status"), int) and r["status"] in match_status and r["length"] > 0
    ]
    if not lengths:
        return 0
    return sum(lengths) / len(lengths)


def keyword_score(url):
    keywords = ["admin", "administrator", "login", "install", "backup", "tmp", "debug", "config"]
    score = 0.0
    lower_url = url.lower()
    for kw in keywords:
        if kw in lower_url:
            score += 0.05  # كل keyword تزود شوية
    return min(score, 0.3)  # سقف للـ keyword score


def status_score(status):
    if not isinstance(status, int):
        return 0.0
    if status in (200, 201):
        return 0.4
    if status in (301, 302, 307):
        return 0.25
    if status in (401, 403):
        return 0.2
    return 0.0


def length_score(length, baseline):
    if baseline <= 0 or length <= 0:
        return 0.0
    # نسبة الاختلاف عن المتوسط
    diff = abs(length - baseline) / baseline
    if diff < 0.1:
        return 0.0
    if diff < 0.3:
        return 0.1
    if diff < 0.6:
        return 0.2
    return 0.3


async def scan_single_base(
    base_url,
    wordlist_path,
    extensions=None,
    match_status=None,
    concurrency=50,
):
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
                return result

        for word in words:
            for ext in extensions:
                path = f"/{word}{ext}"
                full_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
                tasks.append(asyncio.create_task(worker(full_url)))

        # نجمع كل النتائج الأول
        raw_results = await asyncio.gather(*tasks)

        # نحسب baseline length
        baseline = compute_baseline_length(raw_results, match_status)

        enriched_results = []
        for r in raw_results:
            s_score = status_score(r.get("status"))
            l_score = length_score(r.get("length"), baseline)
            k_score = keyword_score(r.get("url", ""))
            total_score = round(s_score + l_score + k_score, 3)
            r["score"] = total_score

            # نطبع بس الحاجات اللي ليها status مهم وسكور أعلى من 0
            if isinstance(r.get("status"), int) and r["status"] in match_status and total_score > 0:
                print(f"[+] {r['status']:3} | {r['length']:6} | score={total_score:.2f} | {r['url']}")

            enriched_results.append(r)

        return enriched_results
