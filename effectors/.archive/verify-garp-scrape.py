#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Verify GARP raw content scrape quality against old files and known concepts."""

import os

VAULT = "/Users/terry/epigenome/chromatin"
MODULES = {
    1: "GARP RAI Module 1 - Raw Content.md",
    2: "GARP RAI Module 2 - Raw Content.md",
    3: "GARP RAI Module 3 - Raw Content.md",
    4: "GARP RAI Module 4 - Raw Content.md",
    5: "GARP RAI Module 5 - Raw Content.md",
}

# Key concepts that MUST appear in each module
MUST_CONTAIN = {
    1: ["Turing", "reinforcement learning", "inscrutability", "deep learning", "supervised"],
    2: [
        "K-means",
        "WCSS",
        "LASSO",
        "Ridge",
        "Elastic Net",
        "logistic regression",
        "confusion matrix",
        "ROC",
        "transformer",
        "Word2Vec",
        "LSTM",
        "backpropagation",
        "silhouette",
        "dendrogram",
        "semi-supervised",
        "co-training",
        "self-training",
    ],
    3: [
        "demographic parity",
        "predictive rate parity",
        "equal opportunity",
        "equalized odds",
        "individual fairness",
        "LIME",
        "SHAP",
        "automation bias",
        "manipulation",
        "existential",
        "reputational",
        "hallucination",
        "sources of unfairness",
    ],
    4: [
        "consequentialism",
        "deontology",
        "virtue ethics",
        "nonmaleficence",
        "beneficence",
        "GDPR",
        "EU AI Act",
        "privacy",
        "governance challenges",
    ],
    5: [
        "data governance",
        "model inventory",
        "three lines",
        "model validation",
        "model documentation",
        "model adaptation",
        "pen and paper",
        "use test",
    ],
}

# Section headings that must exist (from portal TOC)
MUST_HAVE_SECTIONS = {
    1: ["Classical AI", "Neural Net", "Machine Learning"],
    2: [
        "K-Means",
        "Hierarchical",
        "Density",
        "Decision Tree",
        "Neural Network",
        "Semi",
        "Reinforcement",
        "Regularization",
        "NLP",
        "Generative",
    ],
    3: [
        "Bias",
        "Fairness",
        "Explainab",
        "Autonomy",
        "Safety",
        "Reputat",
        "Existential",
        "Global",
        "GenAI",
    ],
    4: [
        "Ethical",
        "Consequentialism",
        "Deontology",
        "Virtue",
        "Nonmaleficence",
        "Privacy",
        "Governance",
        "Regulatory",
    ],
    5: [
        "Data Governance",
        "Model Governance",
        "Model Development",
        "Model Validation",
        "Implementation",
        "GenAI",
    ],
}

print("=" * 60)
print("GARP Raw Content Scrape Verification")
print("=" * 60)

all_ok = True

for n, filename in MODULES.items():
    path = os.path.join(VAULT, filename)
    print(f"\n── Module {n} ──────────────────────────────")

    if not os.path.exists(path):
        print(f"  ❌ FILE MISSING: {filename}")
        all_ok = False
        continue

    with open(path) as f:
        content = f.read()

    lines = content.split("\n")
    headings = [l for l in lines if l.startswith("##")]
    words = len(content.split())

    print(f"  Lines:    {len(lines):,}")
    print(f"  Words:    {words:,}")
    print(f"  Sections: {len(headings)}")

    # Check re-scrape header
    if "Re-scraped:" in content:
        print("  ✅ Fresh scrape marker present")
    else:
        print("  ⚠️  No re-scrape marker — may be original file")

    # Check minimum size (warn if suspiciously small)
    min_words = {1: 3000, 2: 50000, 3: 5000, 4: 4000, 5: 6000}
    if words < min_words[n]:
        print(f"  ❌ TOO SHORT: {words} words (expected >{min_words[n]})")
        all_ok = False
    else:
        print("  ✅ Size OK")

    # Check must-contain concepts
    missing_concepts = []
    for concept in MUST_CONTAIN[n]:
        if concept.lower() not in content.lower():
            missing_concepts.append(concept)
    if missing_concepts:
        print(f"  ❌ MISSING CONCEPTS: {', '.join(missing_concepts)}")
        all_ok = False
    else:
        print(f"  ✅ All key concepts present ({len(MUST_CONTAIN[n])} checked)")

    # Check must-have sections
    missing_sections = []
    for section in MUST_HAVE_SECTIONS[n]:
        if not any(section.lower() in h.lower() for h in headings):
            missing_sections.append(section)
    if missing_sections:
        print(f"  ❌ MISSING SECTIONS: {', '.join(missing_sections)}")
        all_ok = False
    else:
        print(f"  ✅ All expected sections present ({len(MUST_HAVE_SECTIONS[n])} checked)")

    # Print section list
    print("\n  Sections found:")
    for h in headings[:30]:
        print(f"    {h}")
    if len(headings) > 30:
        print(f"    ... and {len(headings) - 30} more")

print("\n" + "=" * 60)
if all_ok:
    print("✅ All checks passed — scrape looks complete")
else:
    print("❌ Issues found — review above before using new files")
print("=" * 60)

# --- Diff against old files (if backed up) ---
print("\n── Diff vs old files ──────────────────────────────────")
print("(Checks what new scrape LOST vs old — regressions matter most)\n")

OLD_BACKUP = os.path.expanduser("~/tmp/garp-backup")
if not os.path.exists(OLD_BACKUP):
    print("  No backup found at ~/tmp/garp-backup — run this first:")
    print("  mkdir ~/tmp/garp-backup")
    for n, filename in MODULES.items():
        print(f'  cp "{VAULT}/{filename}" ~/tmp/garp-backup/m{n}-old.md')
else:
    import subprocess

    for n, filename in MODULES.items():
        old_path = f"{OLD_BACKUP}/m{n}-old.md"
        new_path = os.path.join(VAULT, filename)
        if not os.path.exists(old_path) or not os.path.exists(new_path):
            continue

        result = subprocess.run(
            ["diff", "--unified=0", old_path, new_path], capture_output=True, text=True
        )

        # Count lines removed vs added
        removed = sum(
            1 for l in result.stdout.split("\n") if l.startswith("-") and not l.startswith("---")
        )
        added = sum(
            1 for l in result.stdout.split("\n") if l.startswith("+") and not l.startswith("+++")
        )

        if removed == 0 and added == 0:
            print(f"  M{n}: ✅ Identical to old file")
        elif removed > added * 2:
            print(f"  M{n}: ❌ REGRESSION — lost {removed} lines, gained {added} lines")
            # Show first few removed chunks
            chunks = [
                l
                for l in result.stdout.split("\n")
                if l.startswith("-") and not l.startswith("---")
            ]
            for chunk in chunks[:5]:
                print(f"       {chunk[:120]}")
            all_ok = False
        elif added > removed * 2:
            print(
                f"  M{n}: ✅ NEW CONTENT — gained {added} lines, lost {removed} lines (old scrape was incomplete)"
            )
        else:
            print(f"  M{n}: ⚠️  Changed — -{removed} lines / +{added} lines (review manually)")

print("\n" + "=" * 60)
print("FINAL VERDICT:", "✅ Safe to use" if all_ok else "❌ Review before using")
print("=" * 60)
