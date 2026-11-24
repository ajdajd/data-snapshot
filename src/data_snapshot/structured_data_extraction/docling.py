"""Run local Docling image conversion and retain the native document."""

from pathlib import Path
from typing import Any


def extract_image(
    image_path: Path, *, pipeline: str = "standard", device: str = "cpu"
) -> dict[str, Any]:
    """Convert a PNG through a local Docling pipeline.

    Parameters
    ----------
    image_path : Path
        Existing snapshot image.
    pipeline : str
        ``standard`` for OCR/table recognition or ``granite`` for the small VLM.
    device : str
        ``cpu`` or ``cuda:0``. VLM weights use FP32 on both devices.

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
    accelerator = AcceleratorOptions(device=device, num_threads=4)
    artifacts = settings.cache_dir / "models"
    if not artifacts.is_dir():
        raise FileNotFoundError("Prefetch Docling models before running extraction")
    if pipeline == "standard":
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

    result = DocumentConverter(
        allowed_formats=[InputFormat.IMAGE],
        format_options={InputFormat.IMAGE: image_options},
    ).convert(image_path)
    if result.status != ConversionStatus.SUCCESS:
        raise ValueError(f"Docling conversion did not succeed: {result.status}")
    return result.document.export_to_dict()
