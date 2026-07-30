# Footage sources

Searched for real workplace near-miss video that is openly licensed and actually
downloadable. Two good options found, both better than the YouTube-scrape fallback I
assumed we'd be stuck with. **40 clips are already downloaded** — see `data/`.

---

## ✅ Primary — Mendeley: "Video Dataset for Safe and Unsafe Behaviours"

**Downloaded and verified.** `python src/fetch_footage.py --per-class 5`

| | |
|---|---|
| DOI | [10.17632/xjmtb22pff.1](https://data.mendeley.com/datasets/xjmtb22pff/1) |
| Licence | **CC BY 4.0** — attribution required, commercial use permitted |
| Authors | Oğuzhan Önal, Emre Dandıl — Bilecik Şeyh Edebali Üniversitesi |
| Size | 10.00 GB, 691 clips (mean 14.5 MB) |
| Format | MP4 / H.264, 1920×1080, 24 fps, 1–20 s |
| Source | **Real surveillance footage**, production facility in Eskişehir, Turkey, Nov–Dec 2022, two IP cameras ~4 m above ground |

⚠️ The journal article states CC BY-**NC**; the Mendeley record and its API both return
**CC BY 4.0**. The repository record is authoritative, but if commercialisation ever
matters, resolve it with the authors rather than relying on this note.

### Why this one

Real CCTV at real camera height, not staged training video and not a YouTube rip. But the
reason it's the primary source is the class structure — **every unsafe class has a safe
counterpart**:

| Unsafe | n | Safe counterpart | n |
|---|---|---|---|
| `safe_walkway_violation` | 210 | `safe_walkway` | 75 |
| `opened_panel_cover` | 142 | `closed_panel_cover` | 32 |
| `unauthorized_intervention` | 108 | `authorized_intervention` | 38 |
| `carrying_overload_forklift` | 56 | `safe_carrying` | 30 |

That gives ground truth for the two things we could not otherwise prove:

1. **Extraction accuracy.** Does Pegasus flag the unsafe clips and leave the safe ones
   alone? That's a measured number for the demo instead of an assertion — the same move as
   validating against BDD100K's weather labels.
2. **The absence query, with both halves real.** *"Which conditions appear in unsafe clips
   and never in safe ones"* is the set difference the entire product rests on. Until now
   both sides were synthetic. Here they're real and labelled.

`safe_walkway_violation` (the largest class, 210 clips) maps directly onto the drift pattern
in `src/seed.py` — pedestrian/vehicle proximity with no segregated walkway.

### What's on disk

`data/` — 40 clips, 187 MB, 5 per class, stratified, smallest-first.
`data/manifest.json` — ground-truth label, unsafe flag, paired class, train/test split.
`data/CITATION.txt` — CC BY 4.0 attribution. Keep it.

Verified: all 40 are complete MP4s with intact `mdat`, durations 3.0–10.4 s.

Scale up any time with `--per-class 20` (~700 MB). MP4s are gitignored; the manifest is not.

---

## ✅ Secondary — NVIDIA PhysicalAI SDG-Warehouse (synthetic, huge, multi-camera)

[huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes](https://huggingface.co/datasets/nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes)

| | |
|---|---|
| Licence | **OpenMDW 1.1** (permissive) |
| Total | 18.57 TiB — RGB tier 2.24 TiB |
| Relevant slice | **Forklift–human near-miss: 27,939 clips / 13,410 runs, 10 s each** |
| Rig | 5 ceiling-mounted CCTV-style + 5 worker-height cameras, **10 views per run** |
| Annotations | 2D/3D boxes, camera intrinsics/extrinsics, depth, instance segmentation |
| Access | HF account + `HF_TOKEN` |

```bash
huggingface-cli download nvidia/PhysicalAI-WorldModel-Synthetic-Warehouse-Operations-Scenes \
  --repo-type dataset --include "rgb/forklift_human_nearmiss/**" "metadata/**" \
  --local-dir ./physicalai
```

**Do not run that unfiltered** — even the near-miss RGB slice is roughly 500 GB. Pull one
shard (~5 GB, a few hundred clips) and stop.

### The reason to bother

**Ten synchronised camera angles of the same near-miss run.** That is a direct, ground-truth
test of the project's central technical claim:

> If the fingerprint groups by *causal structure*, ten wildly different views of one run
> collapse into one pattern. If it grouped by *appearance* — which is what embedding
> similarity does — they would not.

We assert that in the README. This dataset lets us **prove** it, with labels, on stage. It's
the strongest validation available anywhere in this search.

Cost: it's rendered, so extraction quality may not transfer to real CCTV, and a judge can
fairly say "that's synthetic." Which is exactly why Mendeley is primary and this is second.

---

## Rejected, and why

| Source | Problem |
|---|---|
| **MOCS** (construction, 41,668 samples, 174 sites) | **Images, not video.** Fails the TwelveLabs test outright |
| Kaggle Construction Site Safety (Roboflow) | Images, YOLOv8 format |
| Construction PPE / heavy-equipment sets | Images |
| **WorkSafeBC / Oregon OSHA / SafetyWorks** video libraries | Hundreds of downloadable videos, but **no stated reuse licence**. Don't build a demo on unclear rights |
| YouTube fail compilations | Downloading violates YouTube ToS, and rights are unclear. Unnecessary now that two openly licensed options exist |

Most construction-safety datasets are images — the same modality trap as camera traps.
Worth remembering as a general rule for this space.

---

## Optional complement — a realistic report corpus

The reporting-gap query needs two inputs: what the cameras saw, and what got filed. The
Mendeley set supplies the first. For the second, OSHA publishes real incident, inspection,
and violation reports (see ["Building Safer Sites", arXiv 2508.09203](https://arxiv.org/html/2508.09203v1),
which aggregates them across all 50 states).

⚠️ These cannot be *joined* to Turkish factory footage — different sites, different
everything. Use them only to calibrate what a real filed report looks like, and keep the
join synthetic. Say so if asked; a fabricated join is exactly the kind of thing a judge will
catch.

---

## Next step

Extraction is now the only unvalidated link in the chain. With `data/` populated and
`data/manifest.json` holding the labels:

```bash
export TL_API_KEY=... TL_INDEX_ID=...
python src/ingest.py --videos data/*.mp4
```

Then score the extracted `sif_potential` against `is_unsafe` in the manifest. That number is
what turns "we think this works" into "we measured it."
