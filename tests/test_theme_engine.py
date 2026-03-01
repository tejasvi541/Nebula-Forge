from nebula_forge.theme_engine import ThemeEngine


def test_theme_engine_returns_default_for_unknown_theme():
    engine = ThemeEngine()
    theme = engine.get_theme("unknown-theme")
    assert theme.key == "tokyo_night"


def test_theme_engine_css_paths_include_base_and_override():
    engine = ThemeEngine()
    paths = engine.css_paths_for("dracula")
    assert paths[0].endswith("themes/tokyo_night.tcss")
    assert paths[1].endswith("themes/overrides/dracula.tcss")
