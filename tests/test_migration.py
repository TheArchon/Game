# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
from pathlib import Path
import ast, json, re

ROOT=Path(__file__).resolve().parents[1]
HEADER="# ║  Powered By  : ArchonNetwork"

def test_all_python_files_parse():
    for path in ROOT.rglob("*.py"):
        if ".pytest_cache" in path.parts: continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

def test_aiogram_is_runtime_dependency():
    req=(ROOT/"requirements.txt").read_text(encoding="utf-8").lower()
    assert "aiogram" in req
    assert "from aiogram" in (ROOT/"app"/"bot.py").read_text(encoding="utf-8")

def test_final_header_is_present_on_every_python_file():
    for path in ROOT.rglob("*.py"):
        if path.name == "__init__.py" or True:
            assert HEADER in path.read_text(encoding="utf-8"), path

def test_all_locales_have_same_surface():
    base=ROOT/"app"/"locales"
    en=json.loads((base/"en.json").read_text())
    for lang in ("en","hi","id","it","ur"):
        d=json.loads((base/f"{lang}.json").read_text())
        assert set(d["buttons"])==set(en["buttons"])
        assert set(d["messages"])==set(en["messages"])
        assert set(d["help"])=={"1","2","3","4","5"}

def test_custom_emoji_text_and_button_paths():
    emoji=(ROOT/"app"/"emoji.py").read_text()
    buttons="\n".join(p.read_text() for p in (ROOT/"app"/"keyboards").glob("*.py"))
    formatting=(ROOT/"app"/"formatting.py").read_text()
    assert "tg-emoji" in emoji
    assert "icon_custom_emoji_id" in buttons
    assert "_TG_RE" in formatting

def test_original_non_secret_file_surface_preserved():
    expected=[
      "app/__init__.py","app/__main__.py","app/config.py","app/db.py","app/emoji.py","app/formatting.py",
      "app/handlers/__init__.py","app/handlers/admin.py","app/handlers/ai.py","app/handlers/callbacks.py","app/handlers/common.py","app/handlers/economy.py","app/handlers/games.py","app/handlers/general.py","app/handlers/help.py","app/handlers/router.py","app/handlers/start.py",
      "app/keyboards/__init__.py","app/keyboards/common.py","app/keyboards/games.py","app/keyboards/help.py","app/keyboards/home.py","app/keyboards/language.py","app/keyboards/profile.py","app/keyboards/wallet.py",
      "app/locales/en.json","app/locales/hi.json","app/locales/id.json","app/locales/it.json","app/locales/loader.py","app/locales/ur.json",
      "app/services/ai.py","app/services/auction.py","app/services/core.py","app/telegram.py","app/updater.py","assets/start.jpg","docker-compose.yml","Dockerfile","LICENSE","README.md","SECURITY.md","VALIDATION.md","requirements.txt","scripts/smoke_test.py","tests/test_core.py","tests/test_imports.py","tests/test_localization.py","tests/test_router.py"
    ]
    assert all((ROOT/p).is_file() for p in expected)
