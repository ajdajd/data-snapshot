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

The three existing models use the PyMuPDF rendering pipeline. Docling Heron uses Docling's native PDF backend, OCR, layout postprocessing, and reading order. This is a comparison of complete pipelines; differences cannot be attributed to layout model weights alone. Only Figure/Table bounds are scored. Native caption/footnote associations are preserved separately and are not scored or used to expand bounds. No custom filtering or association rules were added beyond the existing shared area filter.

Sources for this document:

- Original three-model [comparison report](../data/evaluation_runs/pymupdf/paper_benchmark_half/report.md) and adjacent model-specific `reports/corpus.json` and `reports/sources/*.json`.
- Completed [Docling pooled report](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/corpus.json), with [UNHCR](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/unhcr.json), [PRWP](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/prwp.json), and [refugee](../data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/reports/sources/refugee.json) reports.
- Tables generated from the saved JSON reports with [summarize_benchmark.py](../scripts/summarize_benchmark.py), using its `--docling-root` option. When updating, regenerate the four tables from completed runs and retain the methodology and source paths here. Run artifacts under `data/` are local and may not accompany a Git checkout.

## Current findings

DocLayout-YOLO retains the highest overall Figure precision (**0.587**) and recall (**0.802**). Docling Heron reaches **0.442** precision and **0.718** recall, while its matched Figure bounds have the highest mean IoU (**0.836**) and area recall (**0.844**). Better bounds among matched objects do not compensate for missed detections in the detection metrics.

For Tables, Docling Heron has the highest overall precision (**0.521**) and area precision (**0.997**), with recall **0.899**, close to YOLOv26's **0.902**. DocLayout-YOLO retains the highest matched Table IoU (**0.838**) and area recall (**0.845**). Docling has the highest Table precision in each corpus and the highest Table recall on refugee PADs (**0.841**).

## Figure overall

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron |
|---|---|---:|---:|---:|---:|---:|
| Detection | Precision |  | **0.587** | 0.405 | 0.411 | 0.442 |
| Detection | Recall |  | **0.802** | 0.772 | 0.731 | 0.718 |
| Spatial Accuracy | IoU |  | 0.815 | 0.816 | 0.815 | **0.836** |
| Spatial Accuracy | Area Precision |  | **0.996** | 0.989 | 0.989 | 0.991 |
| Spatial Accuracy | Area Recall |  | 0.819 | 0.826 | 0.825 | **0.844** |

## Table overall

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron |
|---|---|---:|---:|---:|---:|---:|
| Detection | Precision |  | 0.474 | 0.503 | 0.468 | **0.521** |
| Detection | Recall |  | 0.886 | 0.885 | **0.902** | 0.899 |
| Spatial Accuracy | IoU |  | **0.838** | 0.822 | 0.831 | 0.829 |
| Spatial Accuracy | Area Precision |  | 0.993 | 0.995 | 0.994 | **0.997** |
| Spatial Accuracy | Area Recall |  | **0.845** | 0.826 | 0.836 | 0.832 |

## Figure by corpus

| Corpus | Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron |
|---|---|---|---:|---:|---:|---:|---:|
| UNHCR / ReliefWeb | Detection | Precision |  | **0.590** | 0.420 | 0.422 | 0.441 |
| UNHCR / ReliefWeb | Detection | Recall |  | **0.788** | 0.762 | 0.715 | 0.708 |
| UNHCR / ReliefWeb | Spatial Accuracy | IoU |  | 0.815 | 0.816 | 0.815 | **0.837** |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Precision |  | **0.995** | 0.987 | 0.988 | 0.989 |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Recall |  | 0.820 | 0.827 | 0.826 | **0.846** |
| PRWP | Detection | Precision |  | **0.689** | 0.487 | 0.465 | 0.678 |
| PRWP | Detection | Recall |  | 0.877 | 0.857 | **0.896** | 0.805 |
| PRWP | Spatial Accuracy | IoU |  | 0.800 | 0.818 | 0.808 | **0.823** |
| PRWP | Spatial Accuracy | Area Precision |  | **0.999** | **0.999** | 0.994 | **0.999** |
| PRWP | Spatial Accuracy | Area Recall |  | 0.800 | 0.819 | 0.813 | **0.824** |
| Refugee PADs | Detection | Precision |  | **0.330** | 0.118 | 0.124 | 0.148 |
| Refugee PADs | Detection | Recall |  | **0.968** | 0.710 | 0.516 | 0.645 |
| Refugee PADs | Spatial Accuracy | IoU |  | **0.895** | 0.820 | 0.879 | 0.883 |
| Refugee PADs | Spatial Accuracy | Area Precision |  | 0.997 | 0.999 | 0.988 | **1.000** |
| Refugee PADs | Spatial Accuracy | Area Recall |  | **0.898** | 0.821 | 0.890 | 0.883 |

## Table by corpus

| Corpus | Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium | Docling Heron |
|---|---|---|---:|---:|---:|---:|---:|
| UNHCR / ReliefWeb | Detection | Precision |  | 0.498 | 0.472 | 0.408 | **0.528** |
| UNHCR / ReliefWeb | Detection | Recall |  | 0.931 | **0.954** | **0.954** | 0.947 |
| UNHCR / ReliefWeb | Spatial Accuracy | IoU |  | **0.886** | 0.859 | 0.877 | 0.877 |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Precision |  | 0.997 | 0.995 | **0.999** | **0.999** |
| UNHCR / ReliefWeb | Spatial Accuracy | Area Recall |  | **0.889** | 0.864 | 0.878 | 0.878 |
| PRWP | Detection | Precision |  | 0.701 | 0.715 | 0.698 | **0.733** |
| PRWP | Detection | Recall |  | 0.923 | **0.942** | 0.938 | 0.923 |
| PRWP | Spatial Accuracy | IoU |  | **0.815** | 0.811 | 0.810 | 0.805 |
| PRWP | Spatial Accuracy | Area Precision |  | 0.998 | 0.999 | 0.998 | **1.000** |
| PRWP | Spatial Accuracy | Area Recall |  | **0.817** | 0.812 | 0.812 | 0.805 |
| Refugee PADs | Detection | Precision |  | 0.318 | 0.359 | 0.343 | **0.371** |
| Refugee PADs | Detection | Recall |  | 0.814 | 0.773 | 0.827 | **0.841** |
| Refugee PADs | Spatial Accuracy | IoU |  | **0.839** | 0.812 | 0.828 | 0.830 |
| Refugee PADs | Spatial Accuracy | Area Precision |  | 0.985 | 0.990 | 0.986 | **0.992** |
| Refugee PADs | Spatial Accuracy | Area Recall |  | **0.854** | 0.820 | 0.841 | 0.837 |

## Docling completion and native links

The saved predictions for all four models contain exactly the manifest's **238 document IDs**, and their ground-truth payloads are identical. Every source and pooled report has empty document-mismatch lists. Docling has **238** document-completion events with matching expected/processed page counts, totaling **3,753 pages**, and **238** native document JSON sidecars.

Docling ran with model revision `8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`, Docling **2.140.0**, CUDA FP32 layout inference, layout batch size **1**, native document concurrency **2**, and RapidOCR English on CPU. Table structure extraction and enrichment were disabled. Recorded cumulative conversion/export times at each source's final document were approximately **69.5 minutes** for UNHCR, **52.3 minutes** for PRWP, and **50.3 minutes** for refugee: **172.1 minutes** combined. These timers exclude some outer-run overhead and provide no controlled speed comparison with the other models.

Native evidence is under `data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/predictions/sources/<source>.native/<PDF filename>.json`. These assembled Docling documents preserve native text and links separately from the metric predictions, including items excluded by the shared area filter.

| Corpus | Native caption references on pictures/tables | Native footnote references on pictures/tables |
|---|---:|---:|
| UNHCR / ReliefWeb | 389 | 51 |
| PRWP | 319 | 123 |
| Refugee PADs | 109 | 45 |
| **Total** | **817** | **219** |

All **1,036** references resolve within their native document JSON. These are reference counts across native pictures/tables, not counts of distinct texts or associations validated by a human. Link correctness and OCR completeness remain unassessed.

The full half-benchmark exports predictions and native JSON, not crop image files. When a crop is requested through Docling's native image API, it uses the item's own bounds: linked captions/footnotes outside those bounds are **not included**. Text already inside the bounds can appear. The earlier nine-PDF trial visually verified two caption examples; it did not establish footnote crop correctness across this half-sample. Verified crop evidence is in `data/evaluation_runs/docling/stability9_20261019/native_crop_examples_verified/`.

The run emitted empty-OCR and dense-vector page-separator warnings. They allow conversion to continue; completion and page coverage do not establish that all text was recognized or that reading order and links are correct. Bounds and native links have not received a page-by-page visual audit of this half-sample.
