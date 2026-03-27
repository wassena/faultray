# FaultRay One-Pager

---

## 日本語版

---

### FaultRay — ゼロリスク・カオスエンジニアリング

> 本番環境に一切触れずに、インフラストラクチャの可用性上限を数学的に証明する。

---

#### 課題

DORA（EU Digital Operational Resilience Act, 2025年1月施行）により、金融機関はICTシステムのレジリエンステストを義務付けられています。しかし、従来のカオスエンジニアリングツールは本番環境に実際の障害を注入するため、テスト自体がダウンタイムリスクを生むジレンマがあります。

#### FaultRayの解決策

**純粋な数学的シミュレーション**により、実障害注入のリスクを完全に排除:

| 特徴 | 詳細 |
|-----|------|
| **ゼロリスク** | YAMLトポロジー定義のみで動作。本番環境に一切触れない |
| **5分で開始** | `pip install faultray` → 即座にシミュレーション実行 |
| **150+シナリオ** | トポロジーから障害シナリオを自動生成 |
| **3-Layer Model** | 可用性上限をSoftware/Hardware/理論限界の3層で定量証明（特許出願済み） |
| **DORA準拠** | 第24条〜第27条対応の監査レポートを自動生成 |
| **AI Agent対応** | LLMエージェントの障害伝播シミュレーション |

#### DORA対応

| DORA条文 | 要件 | FaultRayの対応 |
|---------|------|---------------|
| 第24条 | レジリエンステストプログラム | 150+シナリオの自動生成・実行 |
| 第25条 | テストが事業を阻害しないこと | シミュレーションのみ（本番影響ゼロ） |
| 第26条 | 高度テスト（TLPT） | カスケード障害・依存関係チェーン分析 |
| 第27条 | テスト結果の文書化 | PDF/HTMLレポート自動生成 |

#### ROI

- 従来ツール: **$124,000〜$820,000/年**（ライセンス+環境+人件費+リスクコスト）
- FaultRay Pro: **$3,588/年** → 最大97%コスト削減
- FaultRay Business: **$11,988/年** → 最大99%コスト削減

#### プラン

| Free | Pro ($299/月) | Business ($999/月) |
|------|-------------|-------------------|
| 月5シミュレーション | 月100シミュレーション | 無制限 |
| 5コンポーネント | 50コンポーネント | 無制限 |
| コミュニティサポート | DORAレポートexport | DORA+保険API |
| | メール24hサポート | カスタムSSO |
| | | 専任1hサポート |

#### 次のステップ

1. **デモ**: https://faultray.dev/demo
2. **インストール**: `pip install faultray`
3. **お問い合わせ**: hello@faultray.dev

---

## English Version

---

### FaultRay — Zero-Risk Chaos Engineering

> Mathematically prove your infrastructure's availability ceiling — without touching production.

---

#### The Problem

DORA (EU Digital Operational Resilience Act, enforced January 2025) mandates ICT resilience testing for financial entities. Traditional chaos engineering tools inject real faults into production, creating a paradox where testing itself becomes a downtime risk.

#### FaultRay's Solution

**Pure mathematical simulation** eliminates the risk of real fault injection entirely:

| Feature | Details |
|---------|---------|
| **Zero risk** | Operates from YAML topology definition only. Never touches production |
| **5-minute setup** | `pip install faultray` → Instant simulation execution |
| **150+ scenarios** | Auto-generates failure scenarios from topology |
| **3-Layer Model** | Quantitative availability ceiling proof across Software/Hardware/Theoretical limits (patent pending) |
| **DORA-compliant** | Auto-generates audit reports for Articles 24–27 |
| **AI Agent support** | LLM agent failure propagation simulation |

#### DORA Coverage

| DORA Article | Requirement | FaultRay Coverage |
|-------------|-------------|-------------------|
| Article 24 | Resilience testing program | 150+ auto-generated scenario execution |
| Article 25 | Testing must not disrupt business | Simulation only (zero production impact) |
| Article 26 | Advanced testing (TLPT) | Cascading failure & dependency chain analysis |
| Article 27 | Test result documentation | Auto-generated PDF/HTML reports |

#### ROI

- Traditional tools: **$124,000–$820,000/year** (license + environment + labor + risk cost)
- FaultRay Pro: **$3,588/year** → Up to 97% cost reduction
- FaultRay Business: **$11,988/year** → Up to 99% cost reduction

#### Plans

| Free | Pro ($299/mo) | Business ($999/mo) |
|------|-------------|-------------------|
| 5 simulations/mo | 100 simulations/mo | Unlimited |
| 5 components | 50 components | Unlimited |
| Community support | DORA report export | DORA + Insurance API |
| | Email 24h support | Custom SSO |
| | | Dedicated 1h support |

#### Next Steps

1. **Demo**: https://faultray.dev/demo
2. **Install**: `pip install faultray`
3. **Contact**: hello@faultray.dev
