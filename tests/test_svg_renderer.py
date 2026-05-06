"""
Tests for SVG rendering output.
"""

from datetime import datetime
from xml.etree import ElementTree

from models.pet_models import PetState
from rendering.svg_renderer import SVGRenderer


def make_pet(**updates):
    data = {
        "username": "octocat",
        "hunger": 50,
        "happiness": 50,
        "health": 100,
        "energy": 100,
        "level": 0,
        "xp": 0,
        "stage": "egg",
        "last_updated": datetime.utcnow(),
    }
    data.update(updates)
    return PetState(**data)


def test_render_pet_is_self_contained_well_formed_svg():
    renderer = SVGRenderer()
    svg = renderer.render_pet(make_pet())

    ElementTree.fromstring(svg)

    assert svg.startswith("<svg")
    assert "https://" not in svg
    assert "@import" not in svg
    assert "fonts.googleapis.com" not in svg


def test_render_pet_escapes_username():
    renderer = SVGRenderer()
    svg = renderer.render_pet(make_pet(username="a&b<cat>'\""))

    ElementTree.fromstring(svg)

    assert "a&amp;b&lt;cat&gt;&apos;&quot;" in svg


def test_stat_bar_widths_match_pet_stats():
    renderer = SVGRenderer()
    svg = renderer.render_pet(
        make_pet(hunger=25, happiness=50, health=75, energy=100)
    )

    assert 'width="50.0" height="15" fill="#ff6b6b"' in svg
    assert 'width="100.0" height="15" fill="#ffd93d"' in svg
    assert 'width="150.0" height="15" fill="#6bcf7f"' in svg
    assert 'width="200.0" height="15" fill="#4d96ff"' in svg


def test_all_stages_render_distinct_sprites():
    renderer = SVGRenderer()
    sprites = {
        stage: renderer.get_pet_sprite(stage)
        for stage in ["egg", "baby", "teen", "adult", "legendary"]
    }

    assert len(set(sprites.values())) == 5
    assert "Crown" in sprites["legendary"]
