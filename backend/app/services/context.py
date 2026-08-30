from backend.app.config import settings


def retrieve_context(query: str) -> list[dict]:
    path = settings.root_dir / "backend" / "app" / "knowledge" / "policies.md"
    lines = [line.strip("- ") for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("-")]
    terms = {w.lower().strip(".,:;()") for w in query.split() if len(w) > 3}
    ranked = []
    for line in lines:
        score = sum(1 for t in terms if t in line.lower())
        if score:
            ranked.append((score, line))
    ranked.sort(reverse=True)
    selected = ranked[:3] if ranked else [(0, line) for line in lines[:2]]
    return [{"source": "policies.md", "text": line} for _, line in selected]
