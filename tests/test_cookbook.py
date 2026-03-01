from nebula_forge.cookbook import COOKBOOK_ENTRIES, search_cookbook


def test_cookbook_has_seed_entries():
    ids = {e.id for e in COOKBOOK_ENTRIES}
    assert "git-workflow" in ids
    assert "prompt-engineer" in ids


def test_search_cookbook_matches_tags_and_title():
    results = search_cookbook("prompt")
    assert any(e.id == "prompt-engineer" for e in results)



def test_cookbook_metadata_conversion():
    entry = COOKBOOK_ENTRIES[0]
    meta = entry.to_metadata()
    assert meta.name == entry.name
    assert meta.category == entry.category
    assert meta.model_preference == entry.model_preference
