"""Generate one SVG per stage and a few mood variants for local preview.

Run from repo root:
  python scripts/preview_pet_variations.py

Or from scripts/:
  python preview_pet_variations.py
"""
import sys
from pathlib import Path
from datetime import datetime

# Repo root on path (before any local imports)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from models.pet_models import PetState, PetStage
from rendering.svg_renderer import SVGRenderer


def main():
    out_dir = _REPO_ROOT / "preview_svgs"
    out_dir.mkdir(exist_ok=True)
    renderer = SVGRenderer()
    now = datetime.utcnow()

    # 1) All 5 stages (same stats so only sprite + bars change)
    stages = [
        (PetStage.EGG, 0, 0),
        (PetStage.BABY, 3, 350),
        (PetStage.TEEN, 7, 750),
        (PetStage.ADULT, 13, 1350),
        (PetStage.LEGENDARY, 21, 2200),
    ]
    for stage, level, xp in stages:
        pet = PetState(
            username="preview",
            hunger=50, happiness=50, health=80, energy=80,
            level=level, xp=xp, stage=stage, last_updated=now,
        )
        svg = renderer.render_pet(pet)
        (out_dir / f"stage_{stage.value}.svg").write_text(svg, encoding="utf-8")
        print(f"Wrote {out_dir / f'stage_{stage.value}.svg'}")

    # 2) Mood variants (adult stage, different stat combos)
    mood_pets = [
        ("hungry", PetState(username="preview", hunger=20, happiness=50, health=80, energy=80, level=13, xp=1350, stage=PetStage.ADULT, last_updated=now)),
        ("tired", PetState(username="preview", hunger=50, happiness=50, health=80, energy=20, level=13, xp=1350, stage=PetStage.ADULT, last_updated=now)),
        ("sad", PetState(username="preview", hunger=50, happiness=20, health=80, energy=80, level=13, xp=1350, stage=PetStage.ADULT, last_updated=now)),
        ("great", PetState(username="preview", hunger=80, happiness=85, health=90, energy=90, level=13, xp=1350, stage=PetStage.ADULT, last_updated=now)),
    ]
    for name, pet in mood_pets:
        svg = renderer.render_pet(pet)
        (out_dir / f"mood_{name}.svg").write_text(svg, encoding="utf-8")
        print(f"Wrote {out_dir / f'mood_{name}.svg'}")

    print(f"\nAll SVGs in: {out_dir.absolute()}")
    print("Open the .svg files in a browser to view.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise