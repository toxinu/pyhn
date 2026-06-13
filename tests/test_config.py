import os

from pyhn.config import Config


def test_default_sections_created(tmp_path):
    config = Config(config_dir=str(tmp_path))
    for section in ("keybindings", "interface", "settings", "colors"):
        assert config.parser.has_section(section)


def test_default_values(tmp_path):
    config = Config(config_dir=str(tmp_path))
    # vim-style: k moves up, j moves down
    assert config.parser.get("keybindings", "up") == "k"
    assert config.parser.get("keybindings", "down") == "j"
    assert config.parser.get("settings", "extra_page") == "3"
    assert config.parser.get("settings", "comments_limit") == "50"
    assert config.parser.get("interface", "show_score") == "true"


def test_config_file_written(tmp_path):
    config = Config(config_dir=str(tmp_path))
    assert os.path.exists(config.config_path)


def test_roundtrip_persists_changes(tmp_path):
    first = Config(config_dir=str(tmp_path))
    first.parser.set("settings", "extra_page", "7")
    with open(first.config_path, "w") as f:
        first.parser.write(f)

    second = Config(config_dir=str(tmp_path))
    assert second.parser.get("settings", "extra_page") == "7"


def test_get_palette(tmp_path):
    config = Config(config_dir=str(tmp_path))
    palette = config.get_palette()
    assert palette
    # Each palette entry is (name, foreground, background, monochrome).
    assert all(len(entry) == 4 for entry in palette)
