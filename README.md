# पाणिनि साहित्य — Sanskrit Shloka Analysis

Study **श्रीमद्भगवद्गीता** and **श्रीमद्भागवत** shlok by shlok: verse → padccheda → grammar
(विभक्ति · कारक · प्रत्यय · धातु · उपसर्ग · लिङ्ग · वचन · पुरुष · लकार) → Hindi meaning.

## Run

Browsers block `file://` data loads, so serve the folder:

```bash
cd /Users/dr.ajayshukla/Panini_sahitya
python3 -m http.server 8777
```

Then open http://127.0.0.1:8777/index.html
(If the local data fails, the app auto-falls back to the jsDelivr CDN copy of the repo.)

## Data

- `data/gita.json` — 700 verses **with full grammar analysis** from the repo (auto-rendered).
- `data/bhagavatam.json` — 13,400+ verses, **verse text only** in the source repo.
- `data/bhagavatam-analysis/skandha-N.json` — **machine-generated** grammar for
  Bhagavatam (12 files, lazy-loaded per skandha). Produced locally with the
  [vidyut](https://github.com/ambuda-org/vidyut) Sanskrit toolkit: each surface word is
  looked up in vidyut's dictionary (kosha). ~57% of words get grammar
  (मूल · विभक्ति · कारक · वचन · लिङ्ग, or धातु · लकार · पुरुष); sandhi-joined words are left
  blank. **This is best-effort and needs review** — the app flags it with a ⚠️ banner.
  Edit any verse via "सम्पादित करें"; your edits are saved in LocalStorage and take priority.

### Regenerating the Bhagavatam analysis

```bash
python3 -m venv .venv
.venv/bin/pip install vidyut
.venv/bin/python -c "import vidyut; vidyut.download_data('.venv/vidyut-data')"   # ~77MB
.venv/bin/python tools/generate_bhagavatam_analysis.py                            # ~5s
```
(The `.venv/` folder is large and local-only; safe to delete after generating.)

Source: https://github.com/sanskritsahitya-com/data — refresh with:

```bash
curl -sL https://raw.githubusercontent.com/sanskritsahitya-com/data/master/srimadbhagavadgita/srimadbhagavadgita.json -o data/gita.json
curl -sL https://raw.githubusercontent.com/sanskritsahitya-com/data/master/srimadbhagavatam/srimadbhagavatam.json -o data/bhagavatam.json
```

## Your added content

Everything you type is stored in the browser (`panini_overrides_v1`).
Use **परिचय → निर्यात / आयात** to back it up or move it between machines.

## Notes

- छन्द (chhand) is intentionally not shown for now.
- All meanings are in Hindi Devanagari.
# panini_sahitya
