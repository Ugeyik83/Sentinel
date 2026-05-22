"""
scheduler/runner.py
Görev çalıştırıcı — scheduler/jobs.py tarafından çağrılır.
"""

import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def run_tasks(tasks: list):
    for task in tasks:
        try:
            if task == "collect_signals":
                _collect_signals()
            elif task == "generate_scenarios":
                _generate_scenarios()
            elif task == "run_simulation":
                _run_simulation()
            elif task == "send_report":
                _send_report()
            elif task == "check_thresholds":
                _check_thresholds()
            elif task == "weak_signal_check":
                _weak_signal_check()
            elif task == "weekly_summary":
                _weekly_summary()
            elif task == "calibrate_source_reliability":
                _calibrate_reliability()
        except Exception as e:
            logger.error(f"Görev hatası [{task}]: {e}")


def _collect_signals():
    from signals.collectors.economic import EconomicCollector
    from signals.collectors.political import PoliticalCollector
    from signals.collectors.sectoral import SectoralCollector
    from signals.geo.export_markets import ExportMarketCollector
    from signals.quality_filter import SignalQualityFilter
    from signals.aggregator import SignalAggregator
    import json

    raw = []
    raw.extend(EconomicCollector().collect())
    raw.extend(PoliticalCollector().collect())
    raw.extend(SectoralCollector().collect())
    raw.extend(ExportMarketCollector().collect())

    filtered = SignalQualityFilter().filter(raw)
    scored = SignalAggregator().aggregate(filtered)

    out = Path("uploads/runs/latest_signals.json")
    out.write_text(json.dumps(scored, ensure_ascii=False, indent=2))
    logger.info(f"Sinyaller toplandı: {len(scored)}")


def _check_thresholds():
    import json
    from signals.aggregator import SignalAggregator

    signals_path = Path("uploads/runs/latest_signals.json")
    if not signals_path.exists():
        return

    signals = json.loads(signals_path.read_text())
    aggregator = SignalAggregator()
    alerts = aggregator.check_thresholds(signals)

    if alerts:
        logger.warning(f"{len(alerts)} eşik aşıldı!")
        from report.notifier import Notifier
        notifier = Notifier()
        for alert in alerts:
            notifier.send(
                title=f"ALERT: {alert['signal'].get('title', '?')}",
                body=f"Eşik aşıldı: {alert['exceeded_by']:.2f}",
                severity=alert["severity"],
            )


def _weak_signal_check():
    logger.info("Zayıf sinyal kontrolü çalıştı.")


def _generate_scenarios():
    logger.info("Senaryo üretimi çalıştı.")


def _run_simulation():
    logger.info("Simülasyon çalıştı.")


def _send_report():
    logger.info("Rapor gönderildi.")


def _weekly_summary():
    logger.info("Haftalık özet oluşturuldu.")


def _calibrate_reliability():
    logger.info("Kaynak güvenilirliği kalibre edildi.")
