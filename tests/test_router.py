# ╔══════════════════════════════════════════════════════════════╗
# ║                         🎮 GAMEBOT                          ║
# ║              Advanced Telegram Gaming Bot                  ║
# ║                                                              ║
# ║  Powered By  : ArchonNetwork                                ║
# ║  Developer   : @ArchonCEO                                   ║
# ║  License     : MIT                                          ║
# ╚══════════════════════════════════════════════════════════════╝
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_all_original_handler_modules_exist():
    names = ["start.py", "help.py", "economy.py", "games.py", "ai.py", "admin.py", "callbacks.py", "router.py", "common.py", "general.py"]
    assert all((ROOT / "app" / "handlers" / name).is_file() for name in names)


def test_all_commands_are_registered_in_modular_handlers():
    expected = {
        "start", "help", "commands", "profile", "wallet", "amount", "leaderboard",
        "checkin", "invite", "flirt", "shayari", "steal", "send", "shield", "flip",
        "trust", "bid", "redeem", "resmemory", "resetmemory", "stats", "ai",
        "maintenance", "adminstats", "addcoupon", "setbalance", "ban", "unban",
        "broadcast", "update", "language", "ping",
    }
    found = set()
    for path in (ROOT / "app" / "handlers").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Command":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        found.add(arg.value)
                for kw in node.keywords:
                    if kw.arg in {"commands", "command"} and isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
                        for item in kw.value.elts:
                            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                                found.add(item.value)
    assert "start" not in found
    assert expected - {"start"} <= found
    assert "CommandStart" in (ROOT / "app" / "handlers" / "start.py").read_text(encoding="utf-8")


def test_root_router_assembles_feature_routers():
    text = (ROOT / "app" / "handlers" / "router.py").read_text(encoding="utf-8")
    for name in ["start", "help_handlers", "general", "economy", "games", "ai", "admin", "callbacks"]:
        assert name in text


def test_sources_parse():
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
