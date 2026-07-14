import asyncio
from pathlib import Path
from urllib.parse import urlparse

from core.profile import get_profile
from core.scanner import scan_single_base
from core.output import write_results_json


async def scan_target(base_url, profile, output_dir, backend="native"):
    results_all = []

    base_urls = []
    if profile.base_paths:
        for bp in profile.base_paths:
            base_urls.append(base_url.rstrip("/") + bp)
    else:
        base_urls.append(base_url)

    for url in base_urls:
        for wl in profile.wordlists:
            results = await scan_single_base(
                url,
                wordlist_path=wl,
                extensions=profile.extensions,
                match_status=profile.match_status,
                concurrency=50,
            )
            results_all.extend(results)

    write_results_json(base_url, results_all, output_dir)


def normalize_url(url):
    url = url.strip()
    if not url:
        return None
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url


def load_urls(input_file):
    path = Path(input_file)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    return [u.strip() for u in path.read_text().splitlines() if u.strip()]


def run_engine(args):
    urls = [normalize_url(u) for u in load_urls(args.input)]
    urls = [u for u in urls if u]

    profile = get_profile(args.profile)

    output_dir = Path(args.output or "results")
    output_dir.mkdir(parents=True, exist_ok=True)

    async def runner():
        tasks = []
        for u in urls:
            tasks.append(scan_target(u, profile, output_dir, backend=args.backend))
        await asyncio.gather(*tasks)

    asyncio.run(runner())
