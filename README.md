# SENTINEL

**Signal-driven ENTerprise Intelligence & EvaLuation Network**

AI-Powered Enterprise Resilience Platform — Gerçek zamanlı dış sinyal izleme, erken zayıf sinyal tespiti, dinamik senaryo üretimi, çok-ajanlı kurumsal simülasyon, otomatik aksiyon önerileri ve kurumsal hafıza ile karar destek sistemi.

---

## Ne Yapar?

```
Dış Dünya (ekonomi, politika, sektör, ihracat pazarları)
        ↓ kalite filtresi + güvenilirlik ağırlıklı skorla
        ↓ eşik bazlı alert + erken zayıf sinyal tespiti
Senaryo üret (güven skoru + validasyon + memory few-shot)
        ↓ hallucination guard → geçersizse reject
Graf üzerinde risk yayılım motoru (typed edges)
        ↓ "Kur artışı → tedarik → maliyet → iş kazası"
Şirket içi simülasyon (org chart bazlı CrewAI ajanları)
        ↓ çatışma logu → kurumsal kültür röntgeni
Aksiyon önerileri (etki × güven × maliyet × geçmiş kanıt)
        ↓ red team stress test (Faz 4)
Otomatik rapor → PDF / E-posta / Slack
        ↓ sonucu kaydet → karar parametresi → sistemi geliştir
```

---

## Temel Özellikler

### Sinyal Katmanı
- **Kalite filtresi** — Clickbait, sansasyonel ve tekrar eden içerik otomatik filtrelenir, reliability skoru düşürülür
- **Güvenilirlik ağırlıklı skorlama** — TCMB ≠ random RSS. Tier bazlı + geçmiş doğruluğa göre dinamik reliability
- **Dinamik kaynak kalibrasyonu** — Her kaynağın geçmiş doğruluğu izlenir, reliability skoru otomatik güncellenir
- **Erken Zayıf Sinyal Tespiti** — Eşik aşılmadan önce pattern değişimini yakalar. Reaktif sistemden proaktif sisteme geçiş

### Graf Katmanı
- **Typed Edge Graf** — SUPPLIES, DEPENDS_ON, OWNS, APPROVES, AUDITS, BLOCKS, REQUIRES, IMPACTS, TRIGGERS, MITIGATES... Her soru bir graf sorgusuna dönüşür
- **Risk Propagation Engine** — Bir node'daki değişim tüm bağlı node'lara yayılır. Edge tipine göre katsayı, sönümlü BFS
- **Schema Evolution** — Yeni belgeler yüklendiğinde şema otomatik güncelleme önerileri üretir. Onay mekanizması ile kontrollü evrim

### Senaryo Katmanı
- **Scenario Confidence Score** — 6 metrik: kanıt sayısı, sinyal tazeliği, kaynak çeşitliliği, geçmiş emsal, graf temellendirmesi, LLM certainty
- **Hallucination Guard** — Graf bağlantısı zorunluluğu, minimum kanıt eşiği, çelişki tespiti. Geçersiz senaryo reject
- **Memory few-shot context** — Geçmiş dersler karar parametresi olarak senaryo prompt'una girer

### Simülasyon Katmanı
- **Dinamik org chart entegrasyonu** — PPTX + DOCX'ten CrewAI ajan hiyerarşisi otomatik kurulur
- **İki simülasyon modu** — Hiyerarşik (CEO → CFO/CIO/ISG) veya Konsensüs (komite oylaması)
- **Kanıta dayalı persona** — Ajan kişilikleri görev tanımı + geçmiş karar geçmişinden türetilir
- **Çatışma logu** — Ajanlar arası fikir ayrılıkları yapılandırılmış olarak kaydedilir. Kurumsal kültür analizi

### Karar Katmanı
- **Action Recommendation Engine** — Her aksiyon için etki, güven, maliyet, süre, sorumlu ve geçmiş kanıt
- **Red Teaming (Faz 4)** — Sistemin önerdiği aksiyona karşı stres testi. "En güvenli aksiyon nasıl kırılır?"

### Öğrenme Katmanı
- **Memory as Decision Parameters** — Geçmiş dersler sadece doküman değil, makine-okunabilir karar parametresi. Few-shot context olarak prompt'a girer
- **Outcome Tracking** — Tahmin vs gerçek karşılaştırması ile sürekli iyileşme
- **Kurumsal kültür analizi** — Çatışma loglarından bias dağılımı, dominant sesler, karar hızı

---

## Mimari

```
sentinel/
│
├── config/
│   ├── export_markets.yaml          # İhracat pazarı ülkeleri
│   ├── scheduler.yaml               # Zamanlama kuralları
│   ├── notifications.yaml           # E-posta / Slack / Teams
│   ├── thresholds.yaml              # Sinyal eşik değerleri
│   ├── source_reliability.yaml      # Kaynak güvenilirlik tier'ları
│   ├── scenario_validation.yaml     # Hallucination guard kuralları
│   └── propagation_factors.yaml     # Edge tipi × propagation katsayısı
│
├── seed/
│   ├── file_parser.py               # PDF/XLSX/DOCX/PPTX/CSV/JSON
│   ├── entity_extractor.py          # LLM → varlık + typed edge üretimi
│   ├── graph_builder.py             # Ontoloji → typed ağırlıklı graf
│   ├── edge_types.yaml              # İlişki türleri katalogu
│   ├── propagation.py               # Risk yayılım motoru (BFS, sönümlü)
│   └── schema_evolution.py          # Otomatik şema güncelleme önerileri
│
├── signals/
│   ├── collectors/
│   │   ├── economic.py              # TCMB, Yahoo Finance, FRED
│   │   ├── political.py             # GDELT, NewsAPI
│   │   └── sectoral.py              # Batarya, otomotiv, metal RSS
│   ├── geo/
│   │   ├── turkey.py                # TR kur, faiz, haber, BIST
│   │   ├── regional.py              # Orta Doğu, AB, Orta Asya
│   │   ├── global.py                # Fed, petrol, küresel tedarik
│   │   └── export_markets.py        # config/export_markets.yaml'dan
│   ├── aggregator.py                # Ham sinyal → güvenilirlik ağırlıklı feed
│   │                                # score = value × weight × reliability × anomaly
│   ├── quality_filter.py            # Clickbait / spam / duplikasyon filtresi
│   ├── reliability_tracker.py       # Kaynak doğruluk geçmişi + dinamik kalibrasyon
│   └── weak_signal_detector.py      # Anomaly detection — eşik öncesi erken uyarı
│
├── scenarios/
│   ├── catalog/
│   │   ├── internal.yaml            # Şirket içi çatışma senaryoları
│   │   └── regulatory.yaml          # ISO/SASO/KVKK uyumsuzluk
│   ├── generator.py                 # LLM → otomatik senaryo üretimi
│   │                                # Memory few-shot context ile beslenir
│   ├── confidence.py                # Scenario Confidence Score (6 metrik)
│   ├── validator.py                 # Hallucination guard — geçersizse reject
│   └── injector.py                  # Senaryo → CrewAI'a besle
│
├── crew/
│   ├── org_loader.py                # PPTX + DOCX → ajan yapısı
│   ├── agents.py                    # Dinamik ajan üretimi
│   ├── tasks.py                     # Senaryoya göre görev üretimi
│   ├── runner.py                    # Hiyerarşik veya konsensüs
│   │                                # Konfigüre edilebilir zaman ufku
│   ├── persona_builder.py           # Kanıta dayalı persona üretimi
│   ├── conflict_tracker.py          # Ajan çatışma logu + kültür analizi
│   ├── action_engine.py             # Aksiyon önerileri + öncelik skoru
│   └── red_team.py                  # (Faz 4) Stress test — öneriyi kır
│
├── memory/
│   ├── incidents/                   # Gerçek olaylar + alınan aksiyonlar
│   ├── previous_runs/               # Geçmiş simülasyon tahminleri
│   ├── outcomes/                    # Tahmin vs gerçek karşılaştırması
│   ├── lessons_learned/             # LLM tarafından üretilen çıkarımlar
│   ├── embeddings/                  # Vector search (ChromaDB)
│   ├── decision_parameters.py       # Dersler → makine-okunabilir karar param
│   │                                # Few-shot format ile prompt'a girer
│   ├── tracker.py                   # Outcome kayıt + accuracy hesabı
│   ├── retriever.py                 # Semantic search — benzer geçmiş bul
│   └── action_outcomes.py           # Hangi aksiyon ne kadar işe yaradı
│
├── report/
│   ├── report_agent.py              # LLM → rapor içeriği
│   ├── pdf_exporter.py              # WeasyPrint → PDF
│   └── notifier.py                  # E-posta / Slack / Teams
│
├── scheduler/
│   ├── jobs.py                      # APScheduler görev tanımları
│   └── runner.py                    # Sabah 07:00 + alert + haftalık
│
├── streamlit_app/
│   ├── main.py                      # Ana giriş + navigasyon
│   └── pages/
│       ├── dashboard.py             # Sinyal akışı + risk skoru
│       ├── weak_signals.py          # Erken uyarı paneli
│       ├── org_setup.py             # PPTX + DOCX yükleme
│       ├── scenarios.py             # Katalog + otomatik senaryolar
│       ├── simulate.py              # Simülasyon çalıştır + takip
│       ├── propagation.py           # Risk yayılım görselleştirme
│       ├── actions.py               # Aksiyon önerileri
│       ├── report.py                # Rapor görüntüle + export
│       ├── memory.py                # Geçmiş olaylar + outcome giriş
│       ├── culture_analytics.py     # Kurumsal kültür röntgeni
│       ├── schema_evolution.py      # Şema evrim önerileri + onay
│       ├── personas.py              # Ajan kişilik yönetimi
│       ├── red_team.py              # (Faz 4) Stress test sonuçları
│       └── settings.py              # Zamanlama, bildirim, eşik config
│
├── uploads/
│   └── runs/
│       └── <run_id>/
│           ├── manifest.json
│           ├── input/
│           ├── signals/
│           ├── scenarios/
│           ├── simulation/
│           └── report/
│
├── app/
│   ├── config.py                    # Ortam değişkenleri
│   └── run_artifacts.py             # Run dizin yönetimi
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## Veri Akışı

```
DIŞ DÜNYA
├── Ekonomik (TCMB, FRED, Yahoo Finance)
├── Politik (GDELT, NewsAPI)
├── Sektörel (RSS)
└── İhracat pazarları (config/export_markets.yaml)
          ↓
    signals/quality_filter.py
    Clickbait / spam / duplikasyon → reliability düşür
          ↓
    signals/aggregator.py
    score = value × weight × source_reliability × anomaly_factor
          ↓
    ┌─────────────────────────────┐
    │  weak_signal_detector.py   │  ← Eşik öncesi erken uyarı
    │  Anomaly detection          │     Isolation Forest + Z-score
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │  Eşik kontrolü              │  ← Reaktif alert
    │  (thresholds.yaml)          │
    └──────────┬──────────────────┘
               ↓
    memory/decision_parameters.py
    Benzer geçmiş dersler — few-shot format
          ↓
    scenarios/generator.py
    LLM + few-shot context + catalog/*.yaml
          ↓
    scenarios/validator.py          ← Hallucination guard
    Graf bağlantısı + min kanıt        Geçersizse REJECT
    + çelişki kontrolü
          ↓
    scenarios/confidence.py         ← 6 metrik
          ↓
    seed/propagation.py             ← Risk yayılım haritası
    Typed edges üzerinde BFS
          ↓
    crew/org_loader.py + persona_builder.py
    crew/runner.py (Hiyerarşik / Konsensüs)
    crew/conflict_tracker.py        ← Çatışma logu
          ↓
    crew/action_engine.py           ← Aksiyon önerileri
    (Faz 4) crew/red_team.py        ← Stress test
          ↓
    report/report_agent.py → PDF + Markdown
          ↓
    ┌──────────────┐  ┌────────────────────────────┐
    │  notifier    │  │  memory/decision_parameters │
    │  E-posta     │  │  Tahmin + aksiyon kaydı     │
    │  Slack/Teams │  │  30/60/90 gün → outcome     │
    └──────────────┘  │  → reliability kalibre      │
                      │  → kültür analizi güncelle  │
                      └────────────────────────────┘
```

---

## Typed Edge Graf

```yaml
# seed/edge_types.yaml
operasyonel:
  - SUPPLIES        # Tedarikçi → Hammadde
  - DEPENDS_ON      # Süreç → Sistem
  - OWNS            # Birim → Risk
  - REQUIRES        # Operasyon → Sertifika
  - BLOCKS          # Risk A → Risk B

yetki:
  - APPROVES        # YK → Bütçe
  - DELEGATES_TO    # CEO → CFO
  - REPORTS_TO      # Hiyerarşi
  - AUDITS          # Denetim → Süreç

etki:
  - IMPACTS         # Olay → Sonuç
  - TRIGGERS        # Risk → Risk
  - MITIGATES       # Kontrol → Risk (negatif propagation)
  - ESCALATES       # Olay → Daha büyük olay

zaman:
  - PRECEDES        # Olay sırası
  - CONCURRENT_WITH # Eş zamanlı
```

**Örnek sorgular:**
```python
# Bir regülasyon hangi operasyonları etkiler?
graph.query("MATCH (r:Regulation)-[:REQUIRES]->(op:Operation)")

# Siber saldırı hangi risk zincirini tetikler?
graph.query("MATCH (e:Event {type:'cyber'})-[:TRIGGERS*1..4]->(r:Risk)")

# CFO'nun sahip olduğu kritik riskler?
graph.query("MATCH (p {role:'CFO'})-[:OWNS]->(r:Risk) WHERE r.score > 16")
```

---

## Risk Propagation Engine

```yaml
# config/propagation_factors.yaml
edge_propagation:
  TRIGGERS: 0.85      # En yüksek aktarım
  IMPACTS: 0.75
  DEPENDS_ON: 0.70
  BLOCKS: 0.60
  REQUIRES: 0.65
  SUPPLIES: 0.55
  OWNS: 0.30
  APPROVES: 0.20
  MITIGATES: -0.40    # Negatif — riski azaltır
  AUDITS: -0.25
```

**Örnek zincir:**
```
Kur Şoku (USD/TRY +%8)
  ↓ IMPACTS (0.75)
Hammadde Maliyeti Artışı
  ↓ TRIGGERS (0.85)
Bütçe Aşımı
  ↓ TRIGGERS (0.85)
Maliyet Kesintisi Baskısı
  ↓ IMPACTS (0.75)
İSG Yatırımı Kısıntısı
  ↓ TRIGGERS (0.85)
İş Kazası Riski Artışı
```

---

## Schema Evolution

Yeni belge yüklendiğinde sistem mevcut şemayı sorgular:

```
┌─ Schema Evolution Önerileri ─────────────────────┐
│                                                    │
│  🆕 Yeni varlık tipi: "ESG_Auditor"               │
│     4 belgede görüldü                             │
│     [Alt sınıf ekle] [Yeni tip] [Reddet]          │
│                                                    │
│  🆕 Yeni edge tipi: "INSURED_BY"                  │
│     Örnek: Risk_3.1 → Allianz                     │
│     [Yeni tip] [MITIGATES alt-tipi] [Reddet]      │
│                                                    │
│  ✅ Otomatik kabul: "Tier1_Supplier"               │
│     7 belgede görüldü (eşik: 3)                   │
└────────────────────────────────────────────────────┘
```

---

## Sinyal Kalite Filtresi

```
"ŞOK! Dolar 50 TL'ye gidiyor!"
→ Clickbait penalty: 0.6
→ Caps penalty: 0.4
→ Effective reliability: 0.0
→ Sistem bu sinyali görmezden gelir

TCMB: "Politika faizi %50'de sabit tutuldu"
→ Quality penalty: 0
→ Effective reliability: 1.00
→ Sistem tam ağırlık verir
```

---

## Sinyal Skorlama

```python
score = normalized_value * weight * source_reliability * anomaly_factor
```

```yaml
# config/source_reliability.yaml
sources:
  tcmb:       {reliability: 1.00, tier: 1}
  fred:        {reliability: 0.98, tier: 1}
  reuters:     {reliability: 0.85, tier: 2}
  newsapi:     {reliability: 0.70, tier: 3}
  gdelt:       {reliability: 0.75, tier: 3}
  random_rss:  {reliability: 0.30, tier: 4}
```

---

## Scenario Confidence Score

```yaml
scenario:
  confidence: 0.81
  signal_strength: high
  hallucination_risk: low
  breakdown:
    evidence_count:        0.92   # ağırlık: 0.25
    signal_freshness:      0.88   # ağırlık: 0.15
    source_diversity:      0.80   # ağırlık: 0.20
    historical_precedent:  0.75   # ağırlık: 0.20
    graph_grounding:       0.90   # ağırlık: 0.15
    llm_certainty:         0.60   # ağırlık: 0.05 (en az güvenilir)
```

---

## Hallucination Guard

```yaml
# config/scenario_validation.yaml
validation_rules:
  require_graph_path: true
  min_evidence_count: 3
  max_llm_weight: 0.30
  min_source_reliability: 0.60
  require_typed_edges: true
  consistency_checks:
    - no_contradictory_signals
    - temporal_coherence
    - entity_existence
```

---

## Memory as Decision Parameters

Geçmiş dersler few-shot context olarak senaryo prompt'una girer:

```
GEÇMİŞ DERS #1:
Durum: Kur krizi, %20 ani yükseliş
Karar: hedge_increase (%40 oranı)
Sonuç: Nakit erimesi %15'te kaldı (%22 tahmin edilmişti)
Başarı skoru: 0.78

GEÇMİŞ DERS #2:
Durum: Kur krizi, vade uzatma denendi
Karar: maturity_extension
Sonuç: 5/3 vakada başarısız
Başarı skoru: 0.31 → ÖNERİLMEZ
```

**Sistem bir süre sonra:**
> "Bu senaryo 4 geçmiş dersi içeriyor. lesson_2025_q3_001'e göre hedge artışı önerildi. lesson_2024_q4_007'ye göre vade uzatma önerilmedi."

---

## Kurumsal Kültür Analizi

Çatışma loglarından otomatik çıkarım:

```
┌─ Kurumsal Karar Kültürü — Son 6 Ay ─────────────┐
│  47 çatışma loglandı                              │
│                                                    │
│  En çok kazanan:  CEO    %62                      │
│  En çok kaybeden: ISG    %38 ← kritik             │
│                                                    │
│  Bias dağılımı:                                   │
│  Cost:       ████████░░ 42%                       │
│  Growth:     █████░░░░░ 28%                       │
│  Safety:     ████░░░░░░ 18%                       │
│  Compliance: ███░░░░░░░ 12%                       │
│                                                    │
│  Ortalama karar süresi: 2.4 tur                   │
│                                                    │
│  Pattern: "Cost-bias dominant. Safety sesi        │
│  sistematik bastırılıyor. Uzun vadede ISG         │
│  riski yaratır."                                  │
└────────────────────────────────────────────────────┘
```

---

## Action Recommendation Engine

```yaml
recommendations:
  - rank: 1
    type: hedge
    description: "USD pozisyonun %60'ını 90 günlük forward'a bağla"
    expected_impact: 0.42
    confidence: 0.78
    estimated_cost: "180K TL"
    implementation_time_days: 3
    responsible_agent: "CFO"
    priority_score: 8.7           # (Etki × Güven) / (Maliyet × Süre)
    evidence:
      historical:
        - "2024 Q3: hedge %38 koruma sağladı"
        - "2025 Q1: hedge %44 koruma sağladı"
      simulation: "Nakit erimesi %15'e düştü"
      graph: "Kur --IMPACTS--> Nakit Akışı"
    side_effects:
      - "Kur lehimize dönerse fırsat kaybı"
```

---

## Red Teaming (Faz 4)

```yaml
recommendation: "USD pozisyonun %60'ını hedge et"
robustness_score: 0.68

identified_vulnerabilities:
  - "Karşı taraf riski: Hedge bankası iflası"
  - "Kur lehimize dönerse 4M TL fırsat kaybı"
  - "Hedge maliyeti enflasyon hedefini aşıyor"

suggested_hardening:
  - "Hedge'i 2 bankaya böl"
  - "Stop-loss yerine collar stratejisi"
```

---

## Graf Altyapı Skalası

| Node Sayısı | Öneri |
|---|---|
| < 10K | NetworkX (varsayılan) |
| 10K–100K | NetworkX + caching |
| > 100K | Neo4j / Memgraph — aynı API, sıfır kod değişikliği |

Mimari baştan soyutlanmış — geçiş şeffaf.

---

## Geliştirme Fazları

| Faz | Kapsam |
|---|---|
| **Faz 1** | seed + signals + scenarios + crew + report + scheduler |
| **Faz 2** | typed edges + propagation + confidence + validation + memory + weak signal + source reliability + quality filter + decision parameters |
| **Faz 3** | schema evolution + conflict tracker + culture analytics + action engine + persona builder + outcome tracking |
| **Faz 4** | red teaming + adversarial mode + graph backend abstraction |
| **Faz 5** | Neo4j/Memgraph migration (ölçek geldiğinde) |

---

## Kurulum

```bash
git clone <private-repo-url>
cd sentinel
pip install -r requirements.txt
cp .env.example .env        # OPENAI_API_KEY ekle
nano config/export_markets.yaml
streamlit run streamlit_app/main.py
```

---

## Teknoloji Stack

| Katman | Teknoloji |
|---|---|
| **UI** | Streamlit |
| **LLM** | OpenAI GPT-4o |
| **Çok-ajan** | CrewAI (Hierarchical + Consensual) |
| **Graf** | NetworkX + Typed Edges → Neo4j (Faz 5) |
| **Anomaly Detection** | scikit-learn (Isolation Forest) |
| **Vector DB** | ChromaDB |
| **Zamanlama** | APScheduler |
| **PDF** | WeasyPrint |
| **Sinyal** | GDELT, NewsAPI, TCMB, Yahoo Finance, FRED |
| **Depolama** | Lokal JSON + ChromaDB |

---

## Güvenlik

- API key sadece `.env` — Git'e gitmez
- Tüm veriler lokal `uploads/runs/` içinde
- Harici depolama servisi yok
- OpenAI'ya sadece işlenmiş prompt gider

---

## Lisans

Private — Tüm hakları saklıdır.
