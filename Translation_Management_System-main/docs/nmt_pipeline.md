# Human-in-the-Loop NMT & Quality Management

## Pipeline Stages
1. **Content Normalization** – Segment text, detect locale, preserve placeholders/tags.
2. **Pre-Processing** – Apply terminology enforcement, TM/TB lookup for 100% and fuzzy matches.
3. **MT Quality Estimation (MTQE)** – Score each segment using regression/classification models trained on past human edits.
4. **Risk Scoring** – Combine MTQE, content type, sector criticality, and locale complexity into risk band (low/medium/high).
5. **Neural Machine Translation** – Route to appropriate domain-adapted NMT engine (in-house or third-party) with glossary injection.
6. **Human Review Allocation** – Based on risk band:
   - *Low*: automated QA + spot-checking.
   - *Medium*: single human post-edit.
   - *High*: dual review (post-editor + senior reviewer).
7. **Quality Assurance** – Run automated QA (terminology, numbers, punctuation, regex) and MQM tagging by reviewers.
8. **Feedback Loop** – Capture edits, update TM/TB, fine-tune MTQE and NMT models.

## Data Inputs
- **Translation Memory** – Segment database with match scores and context.
- **Term Base** – Multilingual glossary with forbidden terms and preferred translations.
- **Adaptive MT Models** – Baseline transformer models fine-tuned per sector and locale.
- **Reviewer Feedback** – Edit distance, MQM tags, comments.

## MTQE Model Features
| Feature | Description |
| --- | --- |
| Source length | Token count, character length. |
| TM leverage | Fuzzy match score from TM. |
| Domain tag | Sector classification (Legal, BFSI, E-Com). |
| Locale difficulty | Historical post-edit distance for locale. |
| Named entity density | Ratio of named entities requiring protection. |
| Formatting complexity | HTML tag count, placeholder density. |
| MT confidence | NMT model-provided confidence score. |

## Human Reviewer Experience
- CAT editor highlights MTQE risk with color coding.
- Inline MT suggestions with TM/TB side panel.
- Quick actions for MQM error tagging, glossary feedback, and segment comments.
- Integrated `diff` view showing MT vs. final translation for audit.

## Quality Metrics
- **Segment-level**: post-edit distance (HTER), MQM error type, time-to-edit.
- **Job-level**: average risk score, percentage segments auto-approved, reviewer throughput.
- **Vendor-level**: quality trend, SLA compliance, rework rate.

## Continuous Improvement Loop
```
Reviewer Edits --> TM/TB Update --> MTQE Retraining --> NMT Fine-tuning --> Improved MT Output
```

- Schedule nightly model retraining per domain; deploy via canary release.
- Use A/B testing on MT output before global rollout.
- Provide analytics to show ROI of human feedback on MT quality.
