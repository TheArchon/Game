# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
import json
from pathlib import Path
from app.locales.loader import SUPPORTED, load

BASE=Path(__file__).resolve().parents[1]/"app"/"locales"

def test_each_language_is_complete_and_aligned():
    required={"buttons","messages","help","languages"}
    en=load("en")
    for lang in SUPPORTED:
        data=json.loads((BASE/f"{lang}.json").read_text(encoding="utf-8"))
        assert required <= data.keys()
        assert set(data["buttons"]) == set(en["buttons"])
        assert set(data["messages"]) == set(en["messages"])
        assert set(data["help"]) == {"1","2","3","4","5"}

def test_all_ui_files_are_modular():
    root=Path(__file__).resolve().parents[1]/"app"
    expected=["handlers/start.py","handlers/help.py","handlers/economy.py","handlers/games.py","handlers/ai.py","handlers/admin.py","handlers/callbacks.py","keyboards/home.py","keyboards/help.py","keyboards/profile.py","keyboards/wallet.py","keyboards/games.py","keyboards/language.py"]
    assert all((root/item).is_file() for item in expected)
