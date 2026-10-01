from grepzztranslate.config import Config
from grepzztranslate.worker import LookupWorker


def test_incomplete_frozen_bundle_reports_ready_error(qt_app, paths, monkeypatch):
    monkeypatch.setattr("grepzztranslate.worker.sys.frozen", True, raising=False)
    worker = LookupWorker(paths, Config())
    received = []
    worker.ready.connect(received.append)
    worker.initialize()
    assert len(received) == 1
    assert any("程序资源不完整" in warning for warning in received[0])
    assert worker.ocr is None
    worker.loop.close()


def test_ocr_timeout_releases_request(qt_app, paths):
    import asyncio
    from PySide6.QtGui import QImage

    class TimedOutOCR:
        async def recognize(self, image):
            raise TimeoutError()

    worker = LookupWorker(paths, Config())
    worker.ocr = TimedOutOCR()
    worker.lookup = object()
    worker.loop = asyncio.new_event_loop()
    errors = []
    worker.failed.connect(lambda request, message: errors.append((request, message)))
    try:
        worker.process(42, QImage())
        assert errors and errors[0][0] == 42
        assert "超时" in errors[0][1]
    finally:
        worker.loop.close()
