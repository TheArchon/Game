# GameBot Aiogram Deep Audit

## Scope
This build was migrated from the supplied GameBot project while preserving its command, callback, database, localization, AI, economy, game, auction, referral, coupon, admin, updater, and custom-emoji surfaces.

## Architecture
- `app/bot.py`: application lifecycle and feature/business methods.
- `app/handlers/`: real Aiogram Router modules; each feature registers its own handlers.
- `app/keyboards/`: inline keyboard builders and custom-emoji button icons.
- `app/services/`: economy/games/auction/AI domain services.
- `app/locales/`: five locale files.
- `app/emoji.py`: reusable Telegram custom-emoji rendering.
- `app/db.py`: SQLite persistence and transactional operations.

## Automated checks
- Python AST parsing: pass.
- Python compilation: pass.
- Core/economy/game tests: pass.
- Localization tests: pass.
- Static command coverage: pass.
- Modular router assembly: pass.
- Custom emoji formatting tests: pass.

## Live-environment limitation
The audit environment did not have the Aiogram package installed and could not reach package indexes/Telegram. Therefore live Telegram API behavior and real-token startup cannot honestly be certified here. The final deployment must install the pinned dependency set and perform one real startup/test against Telegram.
