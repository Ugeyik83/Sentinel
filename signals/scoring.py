"""
signals/scoring.py

Impact Score ve Uncertainty hesaplama motoru.
Senaryo üretilmeden önce sinyal listesinden otomatik türetilir.
Debate orkestratörü bu skorları protokol seçimi için kullanır.

Tasarım prensipleri:
─────────────────────────────────────────────────────────────
1. IMPACT SCORE  — "Bu sinyal seti IGYA'yı ne kadar etkiler?"
   Kaynak: economic.py change_pct, composite_score, anomaly_factor
   Benchmark: ISO 31000 likelihood × impact matrisi
              Wolters Kluwer 5×5 risk scoring (2026)

2. UNCERTAINTY   — "Bu sinyallere ne kadar güvenebiliriz?"
   Kaynak: source_reliability, quality_score, sinyal çeşitliliği,
           sinyal yaşı (staleness)
   Benchmark: USPTO patent #10339484 — signal strength variance
              SeqAnalysis step detection literatürü

3. DEBATE CONFIDENCE — Debate kalitesinden türetilir (orchestrator'da)
   Bu dosyada değil — ayrı modül.
─────────────────────────────────────────────────────────────
"""

import logging
import math
from datetime import datetime, timezone
from statistics import mean, stdev

logger = logging.getLogger(__name__)

# ── Kategori ağırlıkları ──────────────────────────────────────────────────────
# IGYA için hangi sinyal kategorisi ne kadar kritik
# Batarya + ihracat şirketi profiline göre ayarlandı
CATEGORY_WEIGHTS: dict[str, float] = {
    "economic":      1.00,   # Kur, BIST — direkt P&L etkisi
    "export_market": 0.90,   # İhracat pazarı döviz + sertifikasyon
    "sectoral":      0.80,   # Batarya/otomotiv haberleri
    "political":     0.65,   # Haber, iç siyaset
    "regulatory":    0.85,   # SASO, ISO, KVKK
    "operational":   0.75,   # ERP, üretim, tedarik
}

# ── Metrik bazlı etki çarpanları ─────────────────────────────────────────────
# Belirli metrikler impact'i orantısız etkiler
METRIC_MULTIPLIERS: dict[str, float] = {
    "usd_try_rate":    1.30,   # Ana maliyet kalemi
    "eur_try_rate":    1.20,   # İhracat geliri
    "bist100":         0.85,   # Gösterge — dolaylı etki
    "battery_news":    0.90,   # Sektörel
    "lead_market":     1.10,   # Hammadde — kurşun batarya
    "tr_news":         0.70,   # Haber — daha az direkt
}

# ── Kaynak güvenilirlik taban değerleri (config yoksa) ───────────────────────
FALLBACK_RELIABILITY: dict[str, float] = {
    "yahoo_finance":    0.92,
    "newsapi":          0.65,
    "internal":         0.95,
    "benchmark_minerals": 0.80,
    "metal_bulletin":   0.78,
    "autonews":         0.65,
}


# ═════════════════════════════════════════════════════════════════════════════
# IMPACT SCORE
# ═════════════════════════════════════════════════════════════════════════════

def compute_impact_score(signals: list[dict]) -> dict:
    """
    Sinyal listesinden IGYA'ya kurumsal etki skoru hesapla.

    Returns:
        {
            "impact_score": 0.0–1.0,
            "breakdown": {...},
            "dominant_signals": [...],   # En etkili 3 sinyal
            "trigger_category": str,     # Hangi kategori dominant
        }
    """
    if not signals:
        return _impact_result(0.0, {}, [], "none")

    components = {
        "price_shock":      _price_shock_score(signals),
        "anomaly_density":  _anomaly_density(signals),
        "category_weight":  _weighted_category_score(signals),
        "threshold_breach": _threshold_breach_score(signals),
        "signal_volume":    _signal_volume_score(signals),
    }

    # Ağırlıklı toplam
    weights = {
        "price_shock":      0.35,   # En kritik — direkt maliyet
        "anomaly_density":  0.25,   # Weak signal detector çıktısı
        "category_weight":  0.20,   # Kategori profili
        "threshold_breach": 0.15,   # Eşik aşımı sayısı
        "signal_volume":    0.05,   # Az sinyal → düşük etki
    }

    impact = sum(components[k] * weights[k] for k in components)
    impact = min(round(impact, 3), 1.0)

    # En etkili 3 sinyali bul
    dominant = _find_dominant_signals(signals)

    # Dominant kategori
    cat_scores: dict[str, float] = {}
    for s in signals:
        cat = s.get("category", "other")
        cat_scores[cat] = cat_scores.get(cat, 0) + s.get("composite_score", 0)
    trigger_cat = max(cat_scores, key=cat_scores.get) if cat_scores else "none"

    return _impact_result(impact, components, dominant, trigger_cat)


def _price_shock_score(signals: list[dict]) -> float:
    """
    Fiyat/kur değişim yüzdelerinden şok skoru.
    economic.py'nin change_pct alanını kullanır.
    Nonlinear — %5 değişim 0.5 değil, %12 değişim 0.9+ verir.
    """
    max_shock = 0.0
    for s in signals:
        change_pct = abs(s.get("change_pct", 0))
        if change_pct == 0:
            # composite_score'dan normalize et
            change_pct = s.get("composite_score", 0) * 15

        metric = s.get("metric", "")
        multiplier = METRIC_MULTIPLIERS.get(metric, 1.0)

        # Sigmoid benzeri: küçük değişimler düşük skor, büyük değişimler hızlı yükselir
        shock = (1 - math.exp(-change_pct / 8)) * multiplier
        max_shock = max(max_shock, shock)

    return min(max_shock, 1.0)


def _anomaly_density(signals: list[dict]) -> float:
    """
    Weak signal detector anomaly_factor veya z_score içeren sinyallerin yoğunluğu.
    """
    anomalous = [
        s for s in signals
        if s.get("anomaly_factor", 1.0) > 1.2
        or abs(s.get("z_score", 0)) > 1.5
        or s.get("is_weak_signal", False)
    ]
    if not signals:
        return 0.0
    density = len(anomalous) / len(signals)
    # Ağırlıklı — anomaly_factor büyüklüğü de önemli
    avg_factor = mean(
        s.get("anomaly_factor", 1.0) for s in anomalous
    ) if anomalous else 1.0
    return min(density * min(avg_factor / 2, 1.0), 1.0)


def _weighted_category_score(signals: list[dict]) -> float:
    """Her sinyalin composite_score × kategori ağırlığı toplamı."""
    if not signals:
        return 0.0
    weighted_sum = sum(
        s.get("composite_score", 0) * CATEGORY_WEIGHTS.get(s.get("category", ""), 0.5)
        for s in signals
    )
    # Normalize: 10 yüksek etkili sinyal → 1.0
    return min(weighted_sum / 10, 1.0)


def _threshold_breach_score(signals: list[dict]) -> float:
    """
    aggregator.py'nin check_thresholds'undan gelen alert sayısı.
    Sinyalde 'threshold_breached' veya 'severity' alanı varsa kullan.
    """
    breaches = [s for s in signals if s.get("threshold_breached") or s.get("severity") in ("high", "critical")]
    critical = [s for s in breaches if s.get("severity") == "critical"]
    score = min(len(breaches) * 0.15 + len(critical) * 0.25, 1.0)
    return score


def _signal_volume_score(signals: list[dict]) -> float:
    """Az sinyal → düşük güven. Çok sinyal → daha güvenilir etki ölçümü."""
    return min(len(signals) / 20, 1.0)


def _find_dominant_signals(signals: list[dict]) -> list[dict]:
    """En yüksek etki skoru × kategori ağırlığı olan 3 sinyal."""
    scored = []
    for s in signals:
        eff_score = (
            s.get("composite_score", 0)
            * CATEGORY_WEIGHTS.get(s.get("category", ""), 0.5)
            * METRIC_MULTIPLIERS.get(s.get("metric", ""), 1.0)
        )
        scored.append({**s, "_effective_score": eff_score})
    top3 = sorted(scored, key=lambda x: x["_effective_score"], reverse=True)[:3]
    return [
        {
            "title": s.get("title", ""),
            "metric": s.get("metric", ""),
            "category": s.get("category", ""),
            "composite_score": s.get("composite_score", 0),
            "change_pct": s.get("change_pct", 0),
            "effective_impact": round(s["_effective_score"], 3),
        }
        for s in top3
    ]


def _impact_result(score, breakdown, dominant, trigger_cat) -> dict:
    return {
        "impact_score": score,
        "impact_label": _label(score),
        "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
        "dominant_signals": dominant,
        "trigger_category": trigger_cat,
    }


# ═════════════════════════════════════════════════════════════════════════════
# UNCERTAINTY SCORE
# ═════════════════════════════════════════════════════════════════════════════

def compute_uncertainty(signals: list[dict]) -> dict:
    """
    Sinyal setinin ne kadar belirsiz/güvenilmez olduğunu ölç.
    Yüksek uncertainty → adversarial_deep protokolü + daha fazla Devil's Advocate.

    Bileşenler:
    - source_reliability: Kaynakların tarihsel doğruluğu
    - signal_staleness:   Sinyallerin yaşı (eski = belirsiz)
    - signal_conflict:    Aynı metrikte çelişen sinyaller
    - coverage_gap:       Beklenen sinyal kategorileri eksik mi?
    - quality_variance:   quality_score'ların yüksek varyansı

    Returns:
        {
            "uncertainty": 0.0–1.0,
            "breakdown": {...},
            "missing_categories": [...],
            "conflicting_metrics": [...],
        }
    """
    if not signals:
        return _uncertainty_result(0.8, {}, ["all"], [])

    components = {
        "low_reliability":    _low_reliability_score(signals),
        "staleness":          _staleness_score(signals),
        "signal_conflict":    _conflict_score(signals),
        "coverage_gap":       _coverage_gap_score(signals),
        "quality_variance":   _quality_variance_score(signals),
    }

    weights = {
        "low_reliability":  0.30,
        "staleness":        0.20,
        "signal_conflict":  0.25,
        "coverage_gap":     0.15,
        "quality_variance": 0.10,
    }

    uncertainty = sum(components[k] * weights[k] for k in components)
    uncertainty = min(round(uncertainty, 3), 1.0)

    missing = _find_missing_categories(signals)
    conflicts = _find_conflicting_metrics(signals)

    return _uncertainty_result(uncertainty, components, missing, conflicts)


def _low_reliability_score(signals: list[dict]) -> float:
    """Düşük kaynak güvenilirliği → yüksek uncertainty."""
    reliabilities = []
    for s in signals:
        r = s.get("source_reliability")
        if r is None:
            source = s.get("source", "")
            r = FALLBACK_RELIABILITY.get(source, 0.50)
        reliabilities.append(r)
    avg_reliability = mean(reliabilities) if reliabilities else 0.5
    return max(0.0, 1.0 - avg_reliability)


def _staleness_score(signals: list[dict]) -> float:
    """
    Sinyal yaşı. 24 saatten eski sinyaller uncertainty'i artırır.
    economic.py'nin collected_at alanını kullanır.
    """
    now = datetime.now(timezone.utc)
    ages_hours = []
    for s in signals:
        try:
            collected = datetime.fromisoformat(s.get("collected_at", ""))
            if collected.tzinfo is None:
                collected = collected.replace(tzinfo=timezone.utc)
            age_h = (now - collected).total_seconds() / 3600
            ages_hours.append(age_h)
        except Exception:
            ages_hours.append(48.0)   # Bilinmeyen → eski say

    if not ages_hours:
        return 0.5
    avg_age = mean(ages_hours)
    # 0h → 0.0, 24h → 0.5, 72h → 0.9, 168h → 1.0
    return min(1 - math.exp(-avg_age / 48), 1.0)


def _conflict_score(signals: list[dict]) -> float:
    """
    Aynı metrikte zıt değerler → yüksek uncertainty.
    Örn: iki farklı kaynak USD/TRY için %5 artış ve %3 düşüş rapor ediyorsa.
    """
    metric_changes: dict[str, list[float]] = {}
    for s in signals:
        metric = s.get("metric", "")
        change = s.get("change_pct", s.get("change", 0))
        if metric and change != 0:
            metric_changes.setdefault(metric, []).append(float(change))

    conflict_count = 0
    conflicting = []
    for metric, changes in metric_changes.items():
        if len(changes) < 2:
            continue
        # Zıt işaret → çelişki
        if any(c > 0 for c in changes) and any(c < 0 for c in changes):
            conflict_count += 1
            conflicting.append(metric)
        # Aynı yönde ama yüksek varyans
        elif len(changes) >= 2 and stdev(changes) > abs(mean(changes)) * 0.5:
            conflict_count += 0.5

    return min(conflict_count * 0.25, 1.0)


def _coverage_gap_score(signals: list[dict]) -> float:
    """
    IGYA için beklenen 4 kategori mevcut mu?
    Eksik kategori → daha az bilgi → yüksek uncertainty.
    """
    expected = {"economic", "political", "sectoral", "export_market"}
    present = {s.get("category", "") for s in signals}
    missing_count = len(expected - present)
    return missing_count / len(expected)


def _quality_variance_score(signals: list[dict]) -> float:
    """
    quality_score'ların varyansı yüksekse güvenilirlik karışık → uncertainty artar.
    """
    qualities = [s.get("quality_score", 1.0) for s in signals]
    if len(qualities) < 2:
        return 0.0
    variance = stdev(qualities)
    return min(variance * 2, 1.0)


def _find_missing_categories(signals: list[dict]) -> list[str]:
    expected = {"economic", "political", "sectoral", "export_market", "regulatory"}
    present = {s.get("category", "") for s in signals}
    return sorted(expected - present)


def _find_conflicting_metrics(signals: list[dict]) -> list[str]:
    metric_changes: dict[str, list[float]] = {}
    for s in signals:
        metric = s.get("metric", "")
        change = s.get("change_pct", s.get("change", 0))
        if metric and change != 0:
            metric_changes.setdefault(metric, []).append(float(change))
    return [
        m for m, changes in metric_changes.items()
        if any(c > 0 for c in changes) and any(c < 0 for c in changes)
    ]


def _uncertainty_result(score, breakdown, missing, conflicts) -> dict:
    return {
        "uncertainty": score,
        "uncertainty_label": _label(score, invert=True),
        "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
        "missing_categories": missing,
        "conflicting_metrics": conflicts,
    }


# ═════════════════════════════════════════════════════════════════════════════
# YARDIMCI
# ═════════════════════════════════════════════════════════════════════════════

def _label(score: float, invert: bool = False) -> str:
    """0–1 skoru insan okunabilir etikete çevir."""
    if invert:
        # uncertainty için: yüksek skor = yüksek belirsizlik
        if score >= 0.7:
            return "yüksek"
        if score >= 0.4:
            return "orta"
        return "düşük"
    else:
        if score >= 0.7:
            return "yüksek"
        if score >= 0.4:
            return "orta"
        return "düşük"


def enrich_signals_with_scores(signals: list[dict]) -> tuple[dict, dict]:
    """
    Tek çağrıda hem impact hem uncertainty hesapla.
    Generator'dan çağrılan ana fonksiyon.

    Returns:
        (impact_result, uncertainty_result)
    """
    impact = compute_impact_score(signals)
    uncertainty = compute_uncertainty(signals)

    logger.info(
        f"Sinyal skoru | Impact: {impact['impact_score']} ({impact['impact_label']}) | "
        f"Uncertainty: {uncertainty['uncertainty']} ({uncertainty['uncertainty_label']}) | "
        f"Dominant: {impact['trigger_category']}"
    )
    return impact, uncertainty
