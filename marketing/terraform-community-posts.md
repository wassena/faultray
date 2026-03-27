# Terraform Community Posts

## 1. r/Terraform (70k members)

**Title:**
```
I built a pre-apply resilience checker for Terraform — catches single points of failure and cascade risks before you hit apply
```

**Body:**
```
I kept running into the same problem: terraform plan looks clean, but the change introduces a single point of failure or a cascade path nobody noticed. Twice it caused 2am pages.

So I built a tool that scores your infrastructure's resilience before and after a Terraform change:

    terraform show -json plan.out > plan.json
    faultray tf-check plan.json

    Score Before: 72/100
    Score After:  45/100  (-27 points)

    NEW RISKS:
    - Database is now a single point of failure
    - Cache has no replication (data loss risk)

You can add it to CI in one line:

    faultray tf-check plan.json --fail-on-regression --min-score 60

It works with any Terraform-managed infra (AWS, GCP, Azure, on-prem) because it reasons about the dependency graph in the plan JSON, not cloud APIs.

What it catches: removing replicas, adding cascade dependencies, timeout misconfigurations, accidentally making a replicated service single-instance.

What it doesn't catch: application-level bugs, SQL migrations, race conditions. It only reasons about topology and redundancy.

pip install faultray && faultray demo

https://github.com/mattyopon/faultray

Happy to answer questions. Looking for feedback from anyone using Terraform in CI/CD.
```

---

## 2. HashiCorp Discuss (discuss.hashicorp.com/c/terraform-core)

**Title:**
```
Pre-apply resilience scoring for Terraform plans — open-source tool
```

**Body:**
```
Hi all,

I built an open-source tool that analyzes Terraform plan JSON and scores infrastructure resilience before and after changes. It's designed to catch structural issues (SPOFs, cascade paths, replica miscounts) that plan output doesn't surface.

Basic usage:

    terraform plan -out=plan.out
    terraform show -json plan.out > plan.json
    pip install faultray
    faultray tf-check plan.json

It builds a dependency graph from the plan, simulates 2,000+ failure scenarios in memory, and outputs a before/after resilience score. No cloud credentials needed — it works entirely from the plan JSON.

CI/CD integration:

    faultray tf-check plan.json --fail-on-regression --min-score 60

Currently supports AWS, GCP, and Azure resources. The simulation covers cascade failures, capacity analysis, and availability ceiling computation.

Paper with the formal specification: https://doi.org/10.5281/zenodo.19139911
GitHub: https://github.com/mattyopon/faultray

Would appreciate feedback, especially on what resource types matter most to you.
```

---

## 3. Dev.to #terraform tag (comment on trending posts)

Find trending Terraform posts and leave a useful comment mentioning tf-check where relevant. Don't spam — only comment when genuinely useful.

---

## 4. X/Twitter

```
Built a pre-apply resilience checker for Terraform.

terraform show -json plan.out > plan.json
faultray tf-check plan.json

Catches SPOFs, cascade risks, and replica misconfigurations before you hit apply.

pip install faultray

https://github.com/mattyopon/faultray
```

---

## Feature idea: Financial Impact Report (経営者向け)

ユーザーからのフィードバック: レジリエンススコアだけでなく、障害時の推定損失額を出すべき。

```
╭──────────── FaultRay Financial Impact Report ────────────╮
│                                                           │
│  Resilience Score: 45/100                                 │
│                                                           │
│  Estimated Annual Downtime: 43.8 hours                    │
│  Estimated Annual Loss:     $876,000                      │
│                                                           │
│  Top Risks by Financial Impact:                           │
│  1. Database SPOF        → $420K/year (19.2h downtime)   │
│  2. Cache no replication → $180K/year (8.4h downtime)    │
│  3. LB single instance  → $156K/year (7.2h downtime)    │
│                                                           │
│  Cost to Fix:                                             │
│  1. Add DB replica       → $2,400/year → saves $420K    │
│  2. Add cache replica    → $1,200/year → saves $180K    │
│  3. Add LB instance      → $600/year  → saves $156K     │
│                                                           │
│  ROI of fixes: 178x                                       │
│                                                           │
╰───────────────────────────────────────────────────────────╯
```

This would require:
- Component-level cost-per-hour-of-downtime input (from user or estimated)
- MTBF/MTTR → expected annual downtime calculation (already in availability model)
- Fix cost estimation (based on cloud pricing)
- ROI calculation
