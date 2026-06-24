"""Operaciones PDF: unir, dividir, comprimir. Todo en local."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


def page_count(path: str) -> int:
    return len(PdfReader(path).pages)


def merge(inputs: list[str], output: str) -> str:
    writer = PdfWriter()
    for p in inputs:
        reader = PdfReader(p)
        for page in reader.pages:
            writer.add_page(page)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    return output


def split_each_page(input_path: str, output_dir: str) -> list[str]:
    """Una PDF por cada pagina."""
    reader = PdfReader(input_path)
    stem = Path(input_path).stem
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        path = out / f"{stem}_pag{i}.pdf"
        with open(path, "wb") as f:
            writer.write(f)
        results.append(str(path))
    return results


def split_range(input_path: str, output_path: str, start: int, end: int) -> str:
    """Extrae las paginas de start a end (1-based, inclusive) a un PDF."""
    reader = PdfReader(input_path)
    n = len(reader.pages)
    start = max(1, start)
    end = min(n, end)
    if start > end:
        raise ValueError("Rango de paginas invalido.")
    writer = PdfWriter()
    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


# ---------------------------------------------------------------- comprimir
def compress(input_path: str, output_path: str, quality: int = 60,
             min_image_bytes: int = 40_000) -> tuple[int, int]:
    """Comprime un PDF recomprimiendo sus imagenes y los streams.

    Devuelve (tamano_original, tamano_resultante). Es seguro: si recomprimir
    no mejora (o falla), cae a una compresion solo-de-streams; nunca deja el
    archivo mas grande que el original.
    """
    import pikepdf
    from pikepdf import Name, Pdf, PdfImage
    from PIL import Image  # noqa: F401  (lo usa PdfImage.as_pil_image)

    src_size = Path(input_path).stat().st_size
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    pdf = Pdf.open(input_path)
    try:
        for page in pdf.pages:
            try:
                images = page.images
            except Exception:  # noqa: BLE001
                continue
            for _name, obj in list(images.items()):
                try:
                    _recompress_image(obj, quality, min_image_bytes, Name, PdfImage)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Imagen omitida al comprimir: %s", exc)
        pdf.save(output_path, compress_streams=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)
    finally:
        pdf.close()

    out_size = Path(output_path).stat().st_size
    if out_size >= src_size:
        # No mejoro: guarda solo con compresion de streams (sin tocar imagenes).
        pdf2 = pikepdf.Pdf.open(input_path)
        try:
            pdf2.save(output_path, compress_streams=True,
                      object_stream_mode=pikepdf.ObjectStreamMode.generate)
        finally:
            pdf2.close()
        out_size = Path(output_path).stat().st_size
        # Si aun asi es mayor, deja una copia del original.
        if out_size >= src_size:
            import shutil
            shutil.copyfile(input_path, output_path)
            out_size = Path(output_path).stat().st_size
    return src_size, out_size


def _recompress_image(obj, quality: int, min_bytes: int, Name, PdfImage) -> None:
    raw = bytes(obj.read_raw_bytes()) if hasattr(obj, "read_raw_bytes") else b""
    if raw and len(raw) < min_bytes:
        return  # imagen pequena: no merece la pena (y reduce riesgo)
    pimg = PdfImage(obj)
    pil = pimg.as_pil_image()
    gray = pil.mode in ("L", "1")
    if pil.mode in ("RGBA", "LA", "P"):
        pil = pil.convert("RGB")
    pil = pil.convert("L" if gray else "RGB")
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality, optimize=True)
    obj.write(buf.getvalue(), filter=Name("/DCTDecode"))
    obj.ColorSpace = Name("/DeviceGray") if gray else Name("/DeviceRGB")
    obj.BitsPerComponent = 8
    for key in ("/SMask", "/Decode", "/DecodeParms"):
        if key in obj:
            del obj[key]
