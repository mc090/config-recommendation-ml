# Repository Search Criteria Guide

**Purpose**: This guide provides academic and practical justification for repository selection criteria used in the config-recommendation-ml dataset. It is designed to support thesis methodology sections, enable reproducibility, and help others adapt the approach to different domains.

**Audience**: Thesis reviewers, researchers, practitioners adapting this methodology

---

## Table of Contents

1. [Overview](#overview)
2. [Criterion: MIN_STARS](#criterion-min_stars)
3. [Criterion: Sample Size (MAX_REPOS)](#criterion-sample-size-max_repos)
4. [Criterion: Repository Size Constraints](#criterion-repository-size-constraints)
5. [Criterion: Activity Recency](#criterion-activity-recency)
6. [Criterion: Exclusion Policies](#criterion-exclusion-policies)
7. [Criterion: Language Restriction](#criterion-language-restriction)
8. [Bias Analysis and Limitations](#bias-analysis-and-limitations)
9. [Use Case Recommendations](#use-case-recommendations)
10. [Decision Flowchart](#decision-flowchart)

---

## Overview

Repository selection criteria define which GitHub projects are included in the training dataset. These criteria significantly impact:

- **Dataset quality**: Signal-to-noise ratio, relevance to real-world use cases
- **Dataset diversity**: Coverage of different project types, sizes, maturity levels
- **Collection efficiency**: Time and API costs
- **Model generalization**: What populations the trained model applies to

This guide documents the rationale behind each criterion, known biases, and recommendations for different use cases.

### Current Configuration

```bash
# From .env file
MIN_STARS=10                      # Minimum GitHub stars
MAX_REPOS=1500                    # Target sample size (thesis: 1,500; testing: 10-100)
EXCLUDE_FORKS=true                # Exclude forked repositories
EXCLUDE_ARCHIVED=true             # Exclude archived projects
MAX_TIME_SINCE_UPDATE_DAYS=365    # Recently active (within 1 year)
MIN_SIZE_KB=10                    # Minimum size (excludes trivial repos)
MAX_SIZE_KB=500000                # Maximum size (500 MB, prevents timeouts)

# Hardcoded in src/data/fetch_raw.py
language:Python                   # Python repositories only
```

---

## Criterion: MIN_STARS

### Description
Minimum number of GitHub stars (⭐) required for repository inclusion.

**Current value**: `MIN_STARS=10`

### Academic Justification

**Stars as a quality proxy**: GitHub stars serve as a lightweight, community-validated signal of project quality and real-world relevance. Research in software engineering uses stars as a proxy for:
- Project maturity and stability (Kalliamvakou et al., 2014)
- Community adoption and real-world use
- Signal-to-noise ratio (filters toy projects, homework, abandoned experiments)

**Alignment with SE research**: Studies focusing on "widely-used" or "production" software commonly use star thresholds (typically 10-100) to ensure practical relevance while maintaining sufficient sample sizes.

### Practical Justification

**Quality vs Diversity Trade-off**:
- **Higher thresholds (50-100+)**: Better quality signal, established projects, but excludes emerging tools and niche domains
- **Lower thresholds (0-5)**: Maximum diversity, includes new projects, but introduces noise (homework, experiments, abandoned repos)
- **Middle ground (10-50)**: Balances quality filtering with diversity preservation

**MIN_STARS=10 rationale**:
- Filters out majority of toy/homework projects (which typically have 0-5 stars)
- Retains emerging tools and niche libraries (which may have 10-100 stars)
- Preserves large search space (hundreds of thousands of Python repos have 10+ stars)
- Low enough to avoid severe selection bias toward "famous" libraries

### Known Biases

**Excluded populations**:
- ✗ Brand new projects (< 6 months old, still gaining stars)
- ✗ Niche/specialized tools with small user bases
- ✗ Internal/enterprise projects made public recently
- ✗ High-quality projects with low discoverability

**Included populations**:
- ✓ Established open-source projects (6+ months old with community)
- ✓ Projects with demonstrated real-world use
- ✓ Community-validated tools and libraries

**Implication**: Model trained on "community-validated Python projects," not representative of all Python code (private repos, new projects, niche tools).

### Recommendations

| Use Case | Recommended MIN_STARS | Rationale |
|----------|----------------------|-----------|
| **Master's thesis** | 10-50 | Balance quality and diversity; defensible threshold |
| **Production system** | 50-100 | Focus on established, widely-used patterns |
| **Exploration/Research** | 0-5 | Maximum diversity, willing to handle noise |
| **Quick testing** | 100+ | Small, high-quality sample for fast iteration |

### Sensitivity Analysis (To Be Conducted)

Recommended experiment: Sample 50-100 repos each at MIN_STARS = 0, 10, 50, 100 and compare:
- Label distribution (% with pyproject.toml, Dockerfile, GitHub Actions)
- Feature diversity (variance in file counts, sizes, etc.)
- Anecdotal quality (manual inspection of random samples)

---

## Criterion: Sample Size (MAX_REPOS)

### Description
Total number of repositories to collect for the dataset.

**Current value**: `MAX_REPOS=1500` (thesis target); `MAX_REPOS=10` (testing)

### Academic Justification

**Statistical power requirements**:

For multi-label classification with 27 features and 15 labels:

1. **Rule of thumb (features)**: 10-20 samples per feature
   - 27 features × 20 = **540 minimum samples**
   
2. **Multi-label consideration**: Need sufficient positive examples per label
   - Assuming 10-50% label prevalence (common for config files)
   - Want ≥100 positive examples per label for reliable training
   - 15 labels × 100 = **1,500 samples if 10% prevalence**
   
3. **Train/validation/test splits**: 70/15/15 split requires larger dataset
   - Want ≥500 test samples for stable evaluation
   - 500 / 0.15 = **~3,333 total** (conservative)

4. **K-Fold cross-validation**: k=5 requires each fold to be representative
   - Each fold is ~20% of data
   - Want ≥300 samples per fold
   - 300 × 5 = **1,500 minimum**

**Conclusion**: n=1,500 is a **reasonable thesis target** balancing statistical power with collection feasibility. n=500 is acceptable minimum; n=3,000+ is ideal for publication quality.

### Practical Justification

**Collection time**:
- GitHub Search API: 30 requests/minute (hardcoded limit)
- GitHub Trees API: 60-80 requests/minute (configurable)
- Formula: `Time (minutes) = ceil(MAX_REPOS/100) + (MAX_REPOS × 2) / requests_per_minute`

| MAX_REPOS | Time @ 30 req/min | Time @ 60 req/min |
|-----------|-------------------|-------------------|
| 100 | ~7 min | ~4 min |
| 500 | ~34 min | ~17 min |
| 1,500 | ~102 min (1.7 hrs) | ~51 min |
| 3,000 | ~203 min (3.4 hrs) | ~102 min (1.7 hrs) |

**Recommendation**: n=1,500 is feasible for overnight collection; n=500 for quick tests.

### Known Limitations

- **Label imbalance**: Some labels may have <10% prevalence → need to check after collection
- **Collection failures**: API errors, timeouts may reduce final count by 5-10%
- **Stratification requirements**: Multi-label stratification may need larger samples

### Recommendations

| Use Case | Recommended MAX_REPOS | Rationale |
|----------|----------------------|-----------|
| **Master's thesis** | 1,500-3,000 | Statistical power for 15 labels, robust CV |
| **Quick validation** | 100-500 | Fast iteration, proof of concept |
| **Publication quality** | 5,000+ | High confidence, detailed analysis |
| **Production training** | 10,000+ | Maximum generalization, label diversity |

---

## Criterion: Repository Size Constraints

### Description
Minimum and maximum repository sizes (in KB) for inclusion.

**Current values**: `MIN_SIZE_KB=10`, `MAX_SIZE_KB=500000` (500 MB)

### Academic Justification

**MIN_SIZE_KB=10 (minimum)**:
- **Rationale**: Filters out empty or trivial repositories
- **10 KB threshold**: Approximately 50-100 lines of code (realistic minimum for a functional project)
- **Noise reduction**: Excludes placeholder repos, single-file experiments, template forks

**MAX_SIZE_KB=500000 (maximum)**:
- **Rationale**: Computational feasibility and scope control
- **500 MB threshold**: Generous limit that includes large projects while excluding massive monorepos
- **Risk mitigation**: Prevents timeouts during tarball download and content parsing
- **Scope alignment**: Config recommendation applies to typical projects, not massive enterprise monorepos

### Practical Justification

**Distribution of Python repos** (estimated from GitHub statistics):
- 50th percentile: ~100-500 KB (small library or tool)
- 75th percentile: ~1-5 MB (medium project with tests, docs)
- 90th percentile: ~10-50 MB (large project, multiple packages)
- 95th percentile: ~50-200 MB (very large, potentially monorepo)
- 99th percentile: 200 MB+ (monorepo, includes large assets/data)

**Current limits (10 KB - 500 MB) capture ~95-98% of Python repositories**, excluding only extremes.

### Known Biases

**Excluded by MIN_SIZE_KB=10**:
- ✗ Single-file scripts and utilities (legitimate use cases, but outside thesis scope)
- ✗ Minimal configuration-only repos (not representative of typical projects)

**Excluded by MAX_SIZE_KB=500MB**:
- ✗ Large monorepos (e.g., company-wide repositories)
- ✗ Projects with large binary assets (games, ML models)
- ✗ Aggregated documentation repos

**Implication**: Model trained on "typical Python projects," not applicable to extremes (single scripts, massive monorepos).

### Recommendations

| Use Case | MIN_SIZE_KB | MAX_SIZE_KB | Rationale |
|----------|-------------|-------------|-----------|
| **Standard (thesis)** | 10 | 500,000 | Filters noise, prevents timeouts |
| **Include small tools** | 1 | 500,000 | Capture single-file utilities |
| **Include monorepos** | 10 | 1,000,000+ | Expand to very large projects (slower) |
| **Fast collection** | 50 | 100,000 | Focus on medium-sized projects |

---

## Criterion: Activity Recency

### Description
Maximum time since last repository update (in days).

**Current value**: `MAX_TIME_SINCE_UPDATE_DAYS=365` (1 year)

### Academic Justification

**Motivation**: Capture current development practices, not historical artifacts.

**Rationale for 365 days**:
- **Current practices**: Configuration file formats and tools evolve (e.g., pyproject.toml adoption increased 2020-2024)
- **Active development signal**: Updated within 1 year indicates maintained/active project
- **Standard in SE research**: 6-12 month recency is common in software repository mining studies
- **Avoids obsolete patterns**: Excludes projects using deprecated tools or outdated practices

### Practical Justification

**Trade-off: Recency vs Sample Size**:
- **Shorter window (90-180 days)**: More current practices, smaller search space
- **Longer window (365-730 days)**: Larger sample size, includes stable/complete projects
- **365 days (1 year)**: Sweet spot — recent enough for relevance, large enough for diversity

**Activity patterns**:
- ~40-50% of public repos updated in last 90 days (very active)
- ~60-70% updated in last 180 days (active)
- ~75-85% updated in last 365 days (maintained)
- Remainder: Abandoned, complete/stable, or archived

### Known Biases

**Excluded**:
- ✗ Complete/stable projects with infrequent updates (e.g., mature libraries)
- ✗ Archived projects (intentionally excluded via separate flag)
- ✗ Historical versions of tools for longitudinal studies

**Included**:
- ✓ Actively developed projects
- ✓ Recently maintained libraries
- ✓ Current configuration practices and tool adoption patterns

**Implication**: Model reflects "current development practices in maintained Python projects."

### Recommendations

| Use Case | MAX_TIME_SINCE_UPDATE_DAYS | Rationale |
|----------|---------------------------|-----------|
| **Standard (thesis)** | 365 | Balance recency and sample size |
| **Cutting-edge practices** | 90-180 | Focus on very active development |
| **Stable projects included** | 730+ (2 years) | Include mature, infrequently updated libraries |
| **Historical study** | No limit | Longitudinal analysis of practices over time |

---

## Criterion: Exclusion Policies

### Description
Boolean flags to exclude specific repository types.

**Current values**: `EXCLUDE_FORKS=true`, `EXCLUDE_ARCHIVED=true`

### EXCLUDE_FORKS

**Academic Justification**:
- **Avoid duplicates**: Forks often share identical structure with parent repo
- **Focus on original work**: Primary contributions vs derivative copies
- **Standard practice**: SE research typically excludes forks to prevent data leakage and duplicate patterns

**Practical Justification**:
- **Data quality**: Forks may have incomplete modifications, abandoned mid-fork
- **Independence assumption**: ML training assumes samples are independent; forks violate this
- **Signal-to-noise**: Original repos more likely to have thoughtful configuration choices

**When to include forks**:
- Studying fork divergence patterns
- Very small search space (need all available data)
- Explicitly comparing original vs forked configurations

**Recommendation**: **Keep EXCLUDE_FORKS=true for thesis** (standard practice, defensible choice).

### EXCLUDE_ARCHIVED

**Academic Justification**:
- **Active vs historical**: Archived = explicitly marked "no longer maintained" by owner
- **Current practices**: Want contemporary configuration patterns, not legacy
- **Quality signal**: Archived projects may have outdated or deprecated configurations

**Practical Justification**:
- **Relevance**: Archived projects unlikely to reflect current best practices
- **Completeness**: May have incomplete migrations (e.g., partial pyproject.toml adoption)

**When to include archived**:
- Historical analysis of configuration evolution
- Studying deprecated tools or migration patterns
- Very niche domain with limited non-archived repos

**Recommendation**: **Keep EXCLUDE_ARCHIVED=true for thesis** (focus on active development).

---

## Criterion: Language Restriction

### Description
Limit search to repositories whose primary language (as reported by GitHub API) is Python.

**Current value**: Hardcoded `language:Python` in `src/data/fetch_raw.py`

### Academic Justification

**Label coherence**: 
- Primary labels (`has_pyproject_toml`, `has_github_actions`, `has_dockerfile`) are strongly associated with Python ecosystem
- `pyproject.toml` is Python-specific (PEP 518, PEP 621)
- Configuration patterns vary significantly across languages (e.g., `package.json` for Node.js, `pom.xml` for Java)

**Feature relevance**:
- Features like `num_py_files`, `avg_py_file_len`, `has_requirements_txt` are Python-specific
- Mixing languages introduces language as a confounding variable
- Model would need to learn language-specific patterns, diluting signal

**Problem scope**:
- Well-defined, focused research question: "Configuration recommendation **for Python projects**"
- Avoids scope creep and ambiguous generalization claims
- Standard practice: thesis projects focus on single ecosystem for depth

### Practical Justification

**Data quality**:
- Ensures features are meaningful (e.g., `num_py_files` is always relevant)
- Labels have consistent semantics (pyproject.toml always means Python packaging)

**Model generalization**:
- Clear boundary: Model applies to Python projects, not other languages
- Transparent limitations: Easy to communicate scope to users/reviewers

### Known Limitations

**Does not generalize to**:
- ✗ Non-Python projects (JavaScript, Java, Go, Rust, etc.)
- ✗ Polyglot projects (multiple languages in same repo)
- ✗ Cross-language configuration patterns

**Future work**: Could extend approach to other languages by:
- Collecting separate datasets per language
- Adapting features to be language-agnostic
- Training language-specific models or multi-task model

### Recommendations

| Use Case | Language Restriction | Rationale |
|----------|---------------------|-----------|
| **Thesis (Python focus)** | Python only | Label coherence, well-defined scope |
| **Multi-language system** | One dataset per language | Language-specific features and labels |
| **General tool recommendation** | Language-agnostic features | Requires redesign of feature set |

---

## Bias Analysis and Limitations

### Summary of Excluded Populations

The current criteria exclude the following populations:

1. **Low-star projects** (< MIN_STARS): New, niche, or low-visibility projects
2. **Tiny repos** (< MIN_SIZE_KB): Single-file scripts, minimal examples
3. **Huge repos** (> MAX_SIZE_KB): Large monorepos, projects with binary assets
4. **Inactive projects** (> MAX_TIME_SINCE_UPDATE_DAYS): Abandoned, complete/stable projects
5. **Forked repositories**: Derivative work, potential duplicates
6. **Archived projects**: Explicitly deprecated/unmaintained
7. **Non-Python projects**: All other programming languages
8. **Private repositories**: Not publicly accessible
9. **Repos without git trees**: API access restrictions, broken repos

### Implications for Model Generalization

**The trained model is representative of**:
- ✓ Community-validated Python projects (10+ stars)
- ✓ Recently maintained/active development (updated within 1 year)
- ✓ Typical project sizes (10 KB - 500 MB)
- ✓ Open-source, publicly accessible repositories

**The model may NOT generalize to**:
- ✗ Brand new Python projects (< 6 months old, < 10 stars)
- ✗ Private/enterprise Python codebases
- ✗ Historical Python projects (abandoned > 1 year ago)
- ✗ Extreme sizes (single scripts, massive monorepos)
- ✗ Non-Python projects or polyglot codebases
- ✗ Niche tools with very small user communities

### Mitigation Strategies

1. **Document explicitly**: Clearly state scope and limitations in thesis and model card
2. **Ablation studies** (future work): Test model on low-star or inactive repos to understand performance degradation
3. **User guidance**: Provide clear recommendations on when model applies vs out-of-scope
4. **Transparency**: Report all selection criteria and excluded populations in methodology

### Thesis Defense Strategy

**Anticipated question**: "Why exclude low-star projects? Doesn't that bias your results?"

**Answer template**: 
> "We chose MIN_STARS=10 to balance data quality with diversity. This threshold filters noise (toy projects, homework) while retaining a large, diverse search space (200,000+ Python repos). The resulting model represents 'community-validated Python projects,' which aligns with our intended use case: recommending configurations for production-relevant software. We acknowledge this excludes new and niche projects, which we document as a limitation. Future work could explore model robustness on low-star repos through ablation studies."

---

## Use Case Recommendations

### Use Case Matrix

| Scenario | MIN_STARS | MAX_REPOS | SIZE_KB | UPDATE_DAYS | FORKS | ARCHIVED | Rationale |
|----------|-----------|-----------|---------|-------------|-------|----------|-----------|
| **Master's Thesis (Balanced)** | 10-50 | 1,500 | 10-500,000 | 365 | Exclude | Exclude | Quality + diversity, defensible choices |
| **Quick Proof-of-Concept** | 100+ | 100-200 | 10-500,000 | 365 | Exclude | Exclude | Fast iteration, high-quality signal |
| **Production Training (Quality)** | 50-100 | 5,000+ | 10-500,000 | 180-365 | Exclude | Exclude | Established patterns, wide coverage |
| **Research (Maximum Diversity)** | 0-5 | 3,000+ | 1-1,000,000 | 730 | Include | Exclude | Explore full spectrum, tolerate noise |
| **Cutting-Edge Practices** | 20-50 | 1,000-2,000 | 10-500,000 | 90-180 | Exclude | Exclude | Recent tool adoption, modern patterns |
| **Historical Analysis** | 10+ | 2,000+ | 10-500,000 | No limit | Exclude | Include | Longitudinal study of config evolution |

### Thesis-Specific Recommendations

**For a Master's thesis on configuration recommendation**:

```bash
# Recommended .env settings
MIN_STARS=10                      # Balances quality and diversity
MAX_REPOS=1500                    # Statistical power for 15 labels
EXCLUDE_FORKS=true                # Standard practice, avoid duplicates
EXCLUDE_ARCHIVED=true             # Focus on active development
MAX_TIME_SINCE_UPDATE_DAYS=365    # Recent practices, large sample
MIN_SIZE_KB=10                    # Filter trivial repos
MAX_SIZE_KB=500000                # Prevent timeouts, typical projects
```

**Justification for thesis defense**:
- ✅ Statistically justified (n=1,500 for 15 labels, 27 features)
- ✅ Aligned with SE research standards (excludes forks, archived)
- ✅ Balances quality and diversity (MIN_STARS=10 sweet spot)
- ✅ Computationally feasible (collection time ~2-3 hours)
- ✅ Clearly documented biases and limitations
- ✅ Reproducible methodology (all criteria in config)

---

## Decision Flowchart

### Choosing Search Criteria: Step-by-Step Guide

```
START: What is your primary goal?
│
├─→ [Thesis/Academic Research]
│   │
│   ├─→ What's your time budget?
│   │   ├─ Limited (< 1 week): MIN_STARS=50, MAX_REPOS=500-1000
│   │   └─ Adequate (1-2 weeks): MIN_STARS=10, MAX_REPOS=1500-3000
│   │
│   └─→ Recommended settings:
│       • MIN_STARS=10 (defensible, balanced)
│       • MAX_REPOS=1500 (statistical power)
│       • UPDATE_DAYS=365 (standard practice)
│       • EXCLUDE_FORKS=true (avoid duplicates)
│       • See "Thesis-Specific Recommendations" above
│
├─→ [Production System Training]
│   │
│   ├─→ What's your quality requirement?
│   │   ├─ High (proven patterns): MIN_STARS=100+
│   │   └─ Balanced (diverse coverage): MIN_STARS=50
│   │
│   └─→ Recommended settings:
│       • MIN_STARS=50-100 (quality signal)
│       • MAX_REPOS=5000+ (wide coverage)
│       • UPDATE_DAYS=180-365 (current practices)
│       • EXCLUDE_FORKS=true
│
├─→ [Exploration/Research]
│   │
│   └─→ Recommended settings:
│       • MIN_STARS=0-5 (maximum diversity)
│       • MAX_REPOS=2000+ (explore spectrum)
│       • UPDATE_DAYS=730+ (include stable projects)
│       • EXCLUDE_FORKS=false (if studying fork patterns)
│
└─→ [Quick Testing/Prototyping]
    │
    └─→ Recommended settings:
        • MIN_STARS=100+ (high signal)
        • MAX_REPOS=100-200 (fast collection)
        • UPDATE_DAYS=365
        • EXCLUDE_FORKS=true

ALWAYS:
• Document your choices and rationale
• Run pilot test (n=50-100) before full collection
• Monitor label distribution after collection
• Be prepared to adjust if label imbalance is severe (< 5% for any label)
```

### Quick Decision Table

**"I want to..."** → **Use these settings**

| Goal | Settings Preset |
|------|----------------|
| Defend thesis choices rigorously | MIN_STARS=10, MAX_REPOS=1500, standard exclusions |
| Get results fast for demo | MIN_STARS=100, MAX_REPOS=100, standard exclusions |
| Train production model | MIN_STARS=50, MAX_REPOS=5000+, UPDATE_DAYS=180 |
| Explore configuration diversity | MIN_STARS=0, MAX_REPOS=2000+, UPDATE_DAYS=730 |
| Study new tool adoption | MIN_STARS=10, MAX_REPOS=1000, UPDATE_DAYS=90-180 |
| Compare to historical patterns | MIN_STARS=10, MAX_REPOS=2000, no UPDATE_DAYS limit, include archived |

---

## References and Further Reading

### Relevant Literature

- **GitHub repository mining**: Kalliamvakou et al. (2014) "The Promises and Perils of Mining GitHub"
- **Software repository statistics**: Borg et al. (2018) "The MSR cookbook: Mining a decade of research"
- **Sample size for ML**: Beleites et al. (2013) "Sample size planning for classification models"
- **Multi-label learning**: Tsoumakas & Katakis (2007) "Multi-label classification: An overview"

### Related Documentation

- [Dataset Card](./dataset_card.md) - Complete schema and collection details
- [Experiment Plan](./experiment_plan.md) - ML workflow and evaluation strategy
- `.env.example` - Configuration template with inline comments
- [Copilot Instructions](../.github/copilot-instructions.md) - Project overview

---

## Changelog

- **2026-03-26**: Initial version created with comprehensive criteria justification
- (Future updates as criteria are validated through pilot experiments)

---

**Last Updated**: 2026-03-26  
**Document Status**: Initial Draft - To be validated with pilot experiments (Phase 3)
