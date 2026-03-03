# KeyVault

A lightweight, frameless password generator built with Python and PySide6. Passwords are generated in real time as you adjust the controls — no button press required.

---

## Requirements

- Python 3.12+
- PySide6

Install the dependency:

```bash
pip install PySide6
```

---

## Running the app

Both files must be in the same directory.

```bash
python password_generator.py
```

---

## Project structure

```
keyvault/
├── password_generator.py   — UI layer (PySide6)
├── engine.py               — Password logic (no Qt dependency)
└── README.md
```

### engine.py

Contains the `PasswordEngine` class. This is the only file that touches password generation and has no dependency on Qt, so it can be tested or reused independently.

**Generation** uses Python's `secrets` module, which pulls from the operating system's cryptographically secure pseudorandom number generator (CSPRNG). It is suitable for security-sensitive values, unlike `random` which is deterministic and seeded.

The algorithm builds a character pool from whichever sets are enabled, guarantees at least one character from each selected set, fills the remaining length from the full pool, then shuffles the result using `secrets.SystemRandom`.

**Strength scoring** checks length and character set diversity, returning a score from 0 to 100 and a label: Weak, Fair, Strong, or Excellent.

### password_generator.py

The UI layer. Imports `PasswordEngine` from `engine.py` and wires it to the controls. Every slider move and toggle change triggers an immediate regeneration — there is no generate button.

Key implementation details:

- Frameless window using `Qt.FramelessWindowHint` with `WA_TranslucentBackground` for true per-pixel alpha compositing. The rounded corners are painted via a clipped `QPainterPath`, so no rectangular background bleeds through.
- Checkboxes are replaced with a fully custom-painted `TogglePill` widget drawn with `QPainter`. This avoids Qt's default bitmap-based checkbox rendering, which can look soft or low-resolution at non-standard DPI settings.
- Password text transitions use a `QSequentialAnimationGroup` — fade out, swap text, fade in — driven by `QGraphicsOpacityEffect`.
- The strength bar animates its fill width using `QPropertyAnimation` and changes color based on the score.
- Window drag is handled manually via `mousePressEvent` and `mouseMoveEvent` since the title bar is removed.

---

## Controls

| Control | Behavior |
|---|---|
| Length slider | Adjusts password length from 6 to 64 characters |
| Character set toggles | Enable or disable lowercase, uppercase, numbers, and symbols |
| Refresh button (↺) | Generates a new password with the current settings |
| Copy button | Copies the current password to the clipboard |
| Close button (✕) | Closes the application |

The window can be repositioned by clicking and dragging anywhere on it.

---

## Notes

- At least one character set must be active. If all toggles are off, the password field clears and the copy button disables.
- The `engine.py` module has no side effects on import and can be unit tested without a display or Qt installation.
