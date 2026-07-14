import yaml
from pathlib import Path


class Profile:
    def __init__(
        self,
        name,
        description="",
        wordlists=None,
        extensions=None,
        match_status=None,
        ignore_regex=None,
        base_paths=None,
        special_paths=None,
        special_files=None,
    ):
        self.name = name
        self.description = description
        self.wordlists = wordlists or []
        self.extensions = extensions or [""]
        self.match_status = set(match_status or [200, 301, 302, 403])
        self.ignore_regex = ignore_regex or []
        self.base_paths = base_paths or []
        self.special_paths = special_paths or []
        self.special_files = special_files or []

    def __repr__(self):
        return f"<Profile {self.name} wordlists={len(self.wordlists)}>"


def load_profiles(config_path="config/profiles.yaml"):
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Profiles config not found: {config_path}")

    data = yaml.safe_load(path.read_text())
    profiles_data = data.get("profiles", {})

    profiles = {}
    for name, cfg in profiles_data.items():
        profiles[name] = Profile(
            name=name,
            description=cfg.get("description", ""),
            wordlists=cfg.get("wordlists", []),
            extensions=cfg.get("extensions", []),
            match_status=cfg.get("match_status", []),
            ignore_regex=cfg.get("ignore_regex", []),
            base_paths=cfg.get("base_paths", []),
            special_paths=cfg.get("special_paths", []),
            special_files=cfg.get("special_files", []),
        )
    return profiles


def get_profile(name, config_path="config/profiles.yaml"):
    profiles = load_profiles(config_path=config_path)
    if name not in profiles:
        raise ValueError(f"Profile '{name}' not found. Available: {', '.join(profiles.keys())}")
    return profiles[name]
