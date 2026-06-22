from __future__ import annotations

def run_ui() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QLabel
    except Exception as exc:
        raise RuntimeError("PySide6 is required for the graphical UI") from exc
    app=QApplication([]); label=QLabel("Rescue Operator AI - Simulator"); label.resize(420,80); label.show(); return app.exec()
