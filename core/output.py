import json
from pathlib import Path
from urllib.parse import urlparse


def host_from_url(url):
    parsed = urlparse(url)
    return (parsed.netloc or parsed.path).replace(":", "_")


def write_results_json(base_url, results, output_dir):
    host = host_from_url(base_url)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_file = output_dir / f"{host}.json"
    data = {
        "base_url": base_url,
        "results": results,
    }
    out_file.write_text(json.dumps(data, indent=2))
    print(f"[DirFleet] Saved results for {base_url} -> {out_file}")
