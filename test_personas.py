import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from bot.services.persona_service import (
    MALE_PERSONAS,
    FEMALE_PERSONAS,
    get_personas_by_gender,
    get_random_persona,
    get_persona_by_id,
    get_persona_by_name,
    get_persona_by_avatar
)

def test_personas():
    print("🧪 Testing Persona Catalog & Synchronization...")

    assert len(MALE_PERSONAS) == 18, f"Expected 18 male personas, got {len(MALE_PERSONAS)}"
    assert len(FEMALE_PERSONAS) == 20, f"Expected 20 female personas, got {len(FEMALE_PERSONAS)}"

    # Check files exist
    for p in MALE_PERSONAS:
        assert os.path.exists(p.avatar_path), f"Male avatar missing: {p.avatar_path}"
        assert p.name != "", "Persona name cannot be empty"

    for p in FEMALE_PERSONAS:
        assert os.path.exists(p.avatar_path), f"Female avatar missing: {p.avatar_path}"
        assert p.name != "", "Persona name cannot be empty"

    # Test random persona
    m = get_random_persona("male")
    assert m.gender == "male"
    assert os.path.exists(m.avatar_path)

    f = get_random_persona("female")
    assert f.gender == "female"
    assert os.path.exists(f.avatar_path)

    # Test exclude current
    m2 = get_random_persona("male", exclude_name=m.name)
    assert m2.name != m.name

    # Test find by name
    demon = get_persona_by_name("Ночной Демон")
    assert demon is not None
    assert demon.en_name == "Night Demon"
    assert "male_01.jpg" in demon.avatar_path

    cat = get_persona_by_name("Дикая Кошка")
    assert cat is not None
    assert "female_02.jpg" in cat.avatar_path

    # Test find by ID
    p_id = get_persona_by_id("f_07")
    assert p_id is not None
    assert p_id.name == "Опасная Малышка"

    # Test find by avatar
    p_av = get_persona_by_avatar(demon.avatar_path)
    assert p_av is not None
    assert p_av.name == demon.name

    print(f"✅ Successfully tested all {len(MALE_PERSONAS) + len(FEMALE_PERSONAS)} personas!")
    print(f"✨ Sample Male Persona: '{demon.name}' -> {demon.avatar_path}")
    print(f"✨ Sample Female Persona: '{cat.name}' -> {cat.avatar_path}")

if __name__ == "__main__":
    test_personas()
