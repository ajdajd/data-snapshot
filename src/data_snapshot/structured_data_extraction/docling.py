"""Run local Docling image conversion and retain the native document."""

from pathlib import Path
from typing import Any


def _offload_chart_model(model: Any, device: str) -> None:
    """Offload LlavaNext components while retaining its direct image parameter.

    Parameters
    ----------
    model : Any
        Initialized Granite Vision LlavaNext model.
    device : str
        Execution device for image encoding and generation.
    """
    import torch
    from accelerate import cpu_offload

    multimodal = model.model
    # Generation calls the image encoder before this parent's forward hook runs.
    multimodal.image_newline = torch.nn.Parameter(
        multimodal.image_newline.to(device), requires_grad=False
    )
    for component in (*multimodal.children(), model.lm_head):
        cpu_offload(
            component,
            execution_device=torch.device(device),
            offload_buffers=True,
            # MultiheadAttention reads out_proj weights without calling that module.
            preload_module_classes=["MultiheadAttention"],
        )


def extract_image(
    image_path: Path, *, pipeline: str = "standard", device: str = "cpu"
) -> dict[str, Any]:
    """Convert a PNG through a local Docling pipeline.

    Parameters
    ----------
    image_path : Path
        Existing snapshot image.
    pipeline : str
        ``standard`` for OCR/tables, ``granite`` for the small VLM, or
        ``chart`` for standard conversion plus dedicated Chart2CSV enrichment.
    device : str
        ``cpu`` or ``cuda:0``. Chart enrichment uses CPU BF16 or GPU FP16
        with CPU weight offloading; the small Granite model uses FP32.

    Returns
    -------
    dict
        Native Docling document, including detected cells and source references.

    Raises
    ------
    ValueError
        If the pipeline is unknown or conversion is incomplete.
    """
    from docling.datamodel.accelerator_options import (
        AcceleratorDevice,
        AcceleratorOptions,
    )
    from docling.datamodel.base_models import ConversionStatus, InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
    from docling.document_converter import DocumentConverter, ImageFormatOption
    from docling.datamodel.settings import settings

    if device not in {"cpu", "cuda:0"}:
        raise ValueError("Device must be cpu or cuda:0")
    chart_offload = pipeline == "chart" and device == "cuda:0"
    accelerator = AcceleratorOptions(
        device="cpu" if chart_offload else device, num_threads=4
    )
    artifacts = settings.cache_dir / "models"
    if not artifacts.is_dir():
        raise FileNotFoundError("Prefetch Docling models before running extraction")
    if pipeline in {"standard", "chart"}:
        options = PdfPipelineOptions(
            artifacts_path=artifacts,
            accelerator_options=accelerator,
            do_table_structure=True,
            do_ocr=True,
            ocr_options=RapidOcrOptions(
                backend="onnxruntime",
                force_full_page_ocr=True,
                rapidocr_params={"EngineConfig.onnxruntime.use_cuda": False},
            ),
        )
        if pipeline == "chart":
            from docling.datamodel.chart_extraction_options import (
                ChartExtractionVlmEngineOptions,
            )
            from docling.datamodel.vlm_engine_options import (
                TransformersVlmEngineOptions,
            )

            chart = ChartExtractionVlmEngineOptions.from_preset(
                "granite_vision_v3_3",
                engine_options=TransformersVlmEngineOptions(
                    device=AcceleratorDevice.CPU,
                    torch_dtype="float16" if chart_offload else "bfloat16",
                    load_in_8bit=False,
                    compile_model=False,
                ),
            )
            chart.model_spec.max_new_tokens = 2048
            for folder in (
                chart.model_spec.default_repo_id.replace("/", "--"),
                options.picture_classification_options.repo_cache_folder,
            ):
                if not (artifacts / folder).is_dir():
                    raise FileNotFoundError(
                        "Prefetch chart models: uv run --no-sync docling-tools "
                        "models download picture_classifier granite_chart_extraction_v3_3"
                    )
            options.do_chart_extraction = True
            options.generate_picture_images = True
            # Reduce image tokens for CPU inference; retain the original PNG.
            options.images_scale = 0.5
            options.chart_extraction_options = chart
        image_options = ImageFormatOption(pipeline_options=options)
    elif pipeline == "granite":
        from docling.datamodel.pipeline_options import (
            VlmConvertOptions,
            VlmPipelineOptions,
        )
        from docling.datamodel.vlm_engine_options import TransformersVlmEngineOptions
        from docling.pipeline.vlm_pipeline import VlmPipeline

        vlm = VlmConvertOptions.from_preset(
            "granite_docling",
            engine_options=TransformersVlmEngineOptions(
                device=(
                    AcceleratorDevice.CPU if device == "cpu" else AcceleratorDevice.CUDA
                ),
                torch_dtype="float32",
                load_in_8bit=False,
                compile_model=False,
            ),
        )
        vlm.model_spec.prompt = "Convert chart to table."
        vlm.model_spec.max_new_tokens = 2048
        image_options = ImageFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=VlmPipelineOptions(
                artifacts_path=artifacts,
                accelerator_options=accelerator,
                vlm_options=vlm,
            ),
        )
    else:
        raise ValueError(f"Unknown Docling pipeline: {pipeline}")

    converter = DocumentConverter(
        allowed_formats=[InputFormat.IMAGE],
        format_options={InputFormat.IMAGE: image_options},
    )
    if chart_offload:
        import torch
        from docling.models.inference_engines.vlm.transformers_engine import (
            TransformersVlmEngine,
        )
        from docling.models.stages.chart_extraction.granite_vision import (
            ChartExtractionVlmEngineModel,
        )

        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA is unavailable; verify GPU access or use --device cpu"
            )
        converter.initialize_pipeline(InputFormat.IMAGE)
        # shortcut: configure the pinned engine until Docling exposes offload options.
        stages = next(iter(converter.initialized_pipelines.values())).enrichment_pipe
        stage = next(s for s in stages if isinstance(s, ChartExtractionVlmEngineModel))
        engine = stage.engine
        if not isinstance(engine, TransformersVlmEngine) or engine.vlm_model is None:
            raise RuntimeError("Expected an initialized Transformers chart model")
        _offload_chart_model(engine.vlm_model, device)
        engine.device = device
    result = converter.convert(image_path)
    if result.status != ConversionStatus.SUCCESS:
        raise ValueError(f"Docling conversion did not succeed: {result.status}")
    return result.document.export_to_dict()
