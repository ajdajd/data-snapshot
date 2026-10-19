# Half-sample paper benchmark reference

Last updated: **2026-10-19**. This is the working comparison document to update as additional model runs become available. Historical run reports remain unchanged.

## Motivation and sample

We evaluate a fixed, randomly selected half of the PDFs in each corpus so we can test faster and get a directional signal before committing to a full benchmark. Selection is uniform without replacement from sorted filenames, using seed **42**, with one random-number generator consumed in source order: UNHCR, PRWP, then refugee. This is half the documents per corpus, not half the pages or annotations; it is not a substitute for full-benchmark results or a statistical significance test.

The exact PDF and annotation filenames, selection method, seed, and corpus counts are in the committed [file manifest](../src/data_snapshot/evaluation/configs/paper_benchmark_half.json). Keep this manifest fixed for subsequent comparisons. The runner is [evaluate_benchmark_half.py](../scripts/evaluate_benchmark_half.py).

| Corpus | Selected PDFs / full PDFs | Pages | Ground-truth Figures | Ground-truth Tables |
|---|---:|---:|---:|---:|
| UNHCR / ReliefWeb | 169 / 338 | 1,295 | 1,139 | 131 |
| PRWP | 50 / 100 | 1,531 | 154 | 274 |
| Refugee PADs | 19 / 38 | 927 | 31 | 220 |
| **Total** | **238 / 476** | **3,753** | **1,324** | **625** |

## Evaluation and evidence

Evaluation IoU threshold: **0.5**. Detection precision and recall use all predictions and annotations. Spatial metrics are means over matched detections only: IoU measures intersection over union, area precision measures intersection divided by predicted area, and area recall measures intersection divided by ground-truth area. Overall values come from the pooled corpus report, not averages of corpus scores. All runs use the existing minimum predicted-area filter of **0.008** of page area.

Blank cells mean not run; N/A means undefined. Bold marks the best available displayed value, including ties at three decimal places. These highlights are descriptive, not evidence of statistical significance.

The three completed non-Docling models use the PyMuPDF rendering pipeline. Docling Heron and Egret Medium use Docling's native PDF backend, OCR, layout postprocessing, and reading order. Comparisons between these pipelines cannot be attributed to layout model weights alone. Within Docling, Egret reuses Heron's integration and recorded pipeline settings; their processor configurations are identical. Egret uses D-FINE and Heron uses RT-DETRv2, so this comparison measures a checkpoint/model substitution, including architecture, rather than learned weights within one architecture. Only Figure/Table bounds are scored. Native caption/footnote associations are preserved separately and are not scored or used to expand bounds. No custom filtering or association rules were added beyond the existing shared area filter.

Sources for this document:

- Original three-model [comparison report](../data/evaluation_runs/pymupdf/paper_benchmark_half/report.md) and adjacent model-specific `reports/corpus.json` and `reports/sources/*.json`.
- Completed [Docling Heron pooled report](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/corpus.json), with [UNHCR](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/unhcr.json), [PRWP](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/prwp.json), and [refugee](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/refugee.json) reports.
- Completed [Docling Egret Medium pooled report](../data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/reports/corpus.json), with [UNHCR](../data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/reports/sources/unhcr.json), [PRWP](../data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/reports/sources/prwp.json), and [refugee](../data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/reports/sources/refugee.json) reports. The [local run configuration](../data/evaluation_runs/docling/egret_medium_20261019/run_config.json) records the reused temporary artifact root.
- Tables generated from the saved JSON reports with [summarize_benchmark.py](../scripts/summarize_benchmark.py), using its `--docling-root` and `--egret-root` options. When updating, regenerate the four tables from completed runs and retain the methodology and source paths here. Run artifacts under `data/` are local and may not accompany a Git checkout.

## Current findings

DocLayout-YOLO retains the highest overall Figure precision (**0.587**) and recall (**0.802**). Egret Medium reaches **0.421** precision and **0.711** recall, below Heron's **0.442** and **0.718**: decreases of **2.11** and **0.68 percentage points**, respectively, calculated from unrounded metrics. Egret has **9 fewer true positives** and **95 more false positives** than Heron. Heron retains the highest matched Figure mean IoU (**0.836**); Egret has the highest matched area recall (**0.846**). These matched-object metrics do not compensate for missed detections.

For Tables, Egret has the highest overall precision (**0.536**), **1.54 percentage points** above Heron (**0.521**), but lower recall (**0.888** versus **0.899**, a **1.12-point** decrease). This reflects **37 fewer false positives** and **7 fewer true positives**. YOLOv26 retains the highest Table recall (**0.902**), Heron the highest matched area precision (**0.997**), and DocLayout-YOLO the highest matched IoU (**0.838**) and area recall (**0.845**). Egret leads Table precision on UNHCR and refugee PADs; Heron leads on PRWP and retains the highest refugee Table recall (**0.841**).

The Figure changes vary by corpus. Egret improves PRWP recall to **0.838** from Heron's **0.805**, but falls to **0.699** from **0.708** on UNHCR and to **0.516** from **0.645** on refugee PADs. The refugee Figure comparison contains only **31** annotated objects. Egret therefore shows a Table precision/recall tradeoff, rather than a general improvement over Heron.

## Figure overall

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron | Docling Egret Medium |
|---|---|---:|---:|---:|---:|---:|---:|
| Detection | Precision |  | **0.587** | 0.405 | 0.411 | 0.442 | 0.421 |
| Detection | Recall |  | **0.802** | 0.772 | 0.731 | 0.718 | 0.711 |
| Spatial Accuracy | IoU |  | 0.815 | 0.816 | 0.815 | **0.836** | 0.834 |
| Spatial Accuracy | Area Precision |  | **0.996** | 0.989 | 0.989 | 0.991 | 0.987 |
| Spatial Accuracy | Area Recall |  | 0.819 | 0.826 | 0.825 | 0.844 | **0.846** |

## Table overall

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron | Docling Egret Medium |
|---|---|---:|---:|---:|---:|---:|---:|
| Detection | Precision |  | 0.474 | 0.503 | 0.468 | 0.521 | **0.536** |
| Detection | Recall |  | 0.886 | 0.885 | **0.902** | 0.899 | 0.888 |
| Spatial Accuracy | IoU |  | **0.838** | 0.822 | 0.831 | 0.829 | 0.827 |
| Spatial Accuracy | Area Precision |  | 0.993 | 0.995 | 0.994 | **0.997** | 0.994 |
| Spatial Accuracy | Area Recall |  | **0.845** | 0.826 | 0.836 | 0.832 | 0.834 |

## Figure by corpus

| Corpus | Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron | Docling Egret Medium |
|---|---|---|---:|---:|---:|---:|---:|---:|
| UNHCR / ReliefWeb | Detection | Precision |  | **0.590** | 0.420 | 0.422 | 0.441 | 0.433 |
| UNHCR / ReliefWeb | Detection | Recall |  | **0.788** | 0.762 | 0.715 | 0.708 | 0.699 |
| UNHCR / ReliefWeb | Spatial Accuracy | IoU |  | 0.815 | 0.816 | 0.815 | **0.837** | 0.835 |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Precision |  | **0.995** | 0.987 | 0.988 | 0.989 | 0.985 |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Recall |  | 0.820 | 0.827 | 0.826 | 0.846 | **0.849** |
| PRWP | Detection | Precision |  | **0.689** | 0.487 | 0.465 | 0.678 | 0.679 |
| PRWP | Detection | Recall |  | 0.877 | 0.857 | **0.896** | 0.805 | 0.838 |
| PRWP | Spatial Accuracy | IoU |  | 0.800 | 0.818 | 0.808 | **0.823** | **0.823** |
| PRWP | Spatial Accuracy | Area Precision |  | **0.999** | **0.999** | 0.994 | **0.999** | 0.995 |
| PRWP | Spatial Accuracy | Area Recall |  | 0.800 | 0.819 | 0.813 | 0.824 | **0.827** |
| Refugee PADs | Detection | Precision |  | **0.330** | 0.118 | 0.124 | 0.148 | 0.078 |
| Refugee PADs | Detection | Recall |  | **0.968** | 0.710 | 0.516 | 0.645 | 0.516 |
| Refugee PADs | Spatial Accuracy | IoU |  | **0.895** | 0.820 | 0.879 | 0.883 | 0.893 |
| Refugee PADs | Spatial Accuracy | Area Precision |  | 0.997 | 0.999 | 0.988 | **1.000** | 0.999 |
| Refugee PADs | Spatial Accuracy | Area Recall |  | **0.898** | 0.821 | 0.890 | 0.883 | 0.894 |

## Table by corpus

| Corpus | Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron | Docling Egret Medium |
|---|---|---|---:|---:|---:|---:|---:|---:|
| UNHCR / ReliefWeb | Detection | Precision |  | 0.498 | 0.472 | 0.408 | 0.528 | **0.550** |
| UNHCR / ReliefWeb | Detection | Recall |  | 0.931 | **0.954** | **0.954** | 0.947 | 0.916 |
| UNHCR / ReliefWeb | Spatial Accuracy | IoU |  | **0.886** | 0.859 | 0.877 | 0.877 | 0.882 |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Precision |  | 0.997 | 0.995 | **0.999** | **0.999** | **0.999** |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Recall |  | **0.889** | 0.864 | 0.878 | 0.878 | 0.883 |
| PRWP | Detection | Precision |  | 0.701 | 0.715 | 0.698 | **0.733** | 0.730 |
| PRWP | Detection | Recall |  | 0.923 | **0.942** | 0.938 | 0.923 | 0.916 |
| PRWP | Spatial Accuracy | IoU |  | **0.815** | 0.811 | 0.810 | 0.805 | 0.805 |
| PRWP | Spatial Accuracy | Area Precision |  | 0.998 | 0.999 | 0.998 | **1.000** | 0.998 |
| PRWP | Spatial Accuracy | Area Recall |  | **0.817** | 0.812 | 0.812 | 0.805 | 0.807 |
| Refugee PADs | Detection | Precision |  | 0.318 | 0.359 | 0.343 | 0.371 | **0.389** |
| Refugee PADs | Detection | Recall |  | 0.814 | 0.773 | 0.827 | **0.841** | 0.836 |
| Refugee PADs | Spatial Accuracy | IoU |  | **0.839** | 0.812 | 0.828 | 0.830 | 0.822 |
| Refugee PADs | Spatial Accuracy | Area Precision |  | 0.985 | 0.990 | 0.986 | **0.992** | 0.984 |
| Refugee PADs | Spatial Accuracy | Area Recall |  | **0.854** | 0.820 | 0.841 | 0.837 | 0.838 |

## Docling completion and native links

The saved predictions for all five completed models contain exactly the manifest's **238 document IDs**, and their document records, labels, and ground-truth annotations are identical. Regenerated ground-truth timestamps and run IDs can differ. Every source and pooled report has empty document-mismatch lists. Each Docling run has **238** document-completion events with matching expected/processed page counts, totaling **3,753 pages**, and **238** native document JSON sidecars. Egret's source and pooled metrics at IoU 0.5 were recomputed from its saved predictions and matched the reports; its prediction files also passed schema v1.3 validation.

Heron used revision `8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`; Egret Medium used `77ede7cc7bed96d853c58f319734803d6ea2ea5c`. Both recorded Docling **2.140.0**, Transformers **5.20.1**, Torch **2.10.0**, RapidOCR **3.10.0**, and ONNX Runtime **1.23.2**, with CUDA FP32 layout inference, layout batch size **1**, native document concurrency **2**, and RapidOCR English on CPU. Table structure extraction, enrichment, and compilation were disabled. Egret reused the existing temporary Heron environment and OCR assets. All common recorded package versions and pipeline notes match; Egret's additionally recorded Pillow, OpenCV, and Pydantic versions match Heron's saved prepared environment. No optional-component or recorded runtime-version difference was found between these runs.

Recorded cumulative timers at each source's final completed document were:

| Corpus | Heron minutes | Egret Medium minutes |
|---|---:|---:|
| UNHCR / ReliefWeb | 69.5 | 76.0 |
| PRWP | 52.3 | 58.8 |
| Refugee PADs | 50.3 | 47.9 |
| **Total** | **172.1** | **182.7** |

Egret took **10.5 minutes longer overall**, or **6.1%** more elapsed time, calculated from unrounded source timers. It was slower on UNHCR and PRWP and faster on refugee PADs. These timers include pipeline initialization, conversion, and per-document native JSON export, but exclude final prediction/report writing and outer-run overhead. Each model ran once, without controlling system load, caching, or thermal state; this is an observed whole-pipeline timing difference, not a stable speed ranking or an isolated detector measurement.

Heron's native evidence is under `data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/predictions/sources/<source>.native/<PDF filename>.json`; Egret's is under `data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/predictions/sources/<source>.native/<PDF filename>.json`. These assembled Docling documents preserve native text and links separately from the metric predictions, including items excluded by the shared area filter.

| Corpus | Heron caption refs | Heron footnote refs | Egret caption refs | Egret footnote refs |
|---|---:|---:|---:|---:|
| UNHCR / ReliefWeb | 389 | 51 | 413 | 29 |
| PRWP | 319 | 123 | 315 | 65 |
| Refugee PADs | 109 | 45 | 118 | 33 |
| **Total** | **817** | **219** | **846** | **127** |

All **1,036 Heron** and **973 Egret** caption/footnote references on native pictures/tables resolve within their document JSON. These are reference counts, not counts of distinct texts or associations validated by a human. Egret's higher caption count and lower footnote count do not establish better or worse association accuracy. Link correctness and OCR completeness remain unassessed.

The full half-benchmark exports predictions and native JSON, not crop image files. When a crop is requested through Docling's native image API, it uses the item's own bounds: linked captions/footnotes outside those bounds are **not included**. Text already inside the bounds can appear. The earlier nine-PDF trial visually verified two caption examples; it did not establish footnote crop correctness across this half-sample. Verified crop evidence is in `data/evaluation_runs/docling/stability9_20261019/native_crop_examples_verified/`.

The Heron run and Egret smoke/sample trials emitted empty-OCR and dense-vector page-separator warnings. They allow conversion to continue; completion and page coverage do not establish that all text was recognized or that reading order and links are correct. No complete Egret half-run process-output log was available in the inspected run directory, so its native warnings were not exhaustively reviewed. Bounds and native links have not received a page-by-page visual audit of either half-sample run.
