import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from .app import ApplicationController
from .config import Config, ConfigManager
from .paths import PathManager


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GrepzzTranslate")
    app.setQuitOnLastWindowClosed(False)
    paths = PathManager.discover()
    try:
        paths.prepare()
        handler = RotatingFileHandler(paths.logs / "grepzztranslate.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", handlers=[handler])
        lock = QLockFile(str(paths.data / "app.lock"))
        lock.setStaleLockTime(0)
        if not lock.tryLock(100):
            QMessageBox.information(None, "GrepzzTranslate", "本目录的程序已在运行，请使用托盘图标。")
            return 0
        error = ""
        try:
            config = ConfigManager(paths.config).load()
        except Exception as exc:
            logging.exception("Configuration invalid")
            config = Config()
            error = f"config.json 无效，暂时使用默认配置：{exc}"
        logging.info("Application started")
        if "--self-test" in sys.argv:
            from .self_test import run_self_test

            exit_code = run_self_test(app, paths)
            lock.unlock()
            return exit_code
        controller = ApplicationController(app, paths, config)
        if error:
            controller.notify(error)
        exit_code = app.exec()
        lock.unlock()
        return exit_code
    except Exception as exc:
        logging.exception("Startup failed")
        QMessageBox.critical(None, "GrepzzTranslate 启动失败", f"{exc}\n请确认解压目录可写，详细错误见 logs。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
