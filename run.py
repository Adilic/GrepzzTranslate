if __name__ == "__main__":
    try:
        from grepzztranslate.main import main

        raise SystemExit(main())
    except Exception:
        import sys
        import traceback
        from pathlib import Path

        root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        (root / "startup-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
