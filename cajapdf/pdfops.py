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
             min_image_bytes: int = 40_000, max_side: int | None = 1600) -> tuple[int, int]:
    """Comprime un PDF recomprimiendo sus imagenes y los streams.

    `max_side` remuestrea las imagenes cuyo lado mayor supere ese numero de
    pixeles (ahi esta el ahorro real: solo bajar la calidad JPEG apenas reduce
    fotos de camara o disenos a alta resolucion).

    Devuelve (tamano_original, tamano_resultante). Es seguro: si recomprimir
    no mejora (o falla), cae a una compresion solo-de-streams; nunca deja el
    archivo mas grande que el original.
    """
    import pikepdf
    from pikepdf import Name, Pdf, PdfImage
    from PIL import Image  # noqa: F401  (lo usa PdfImage.as_pil_image)

    if Path(input_path).resolve() == Path(output_path).resolve():
        # pikepdf se niega a sobrescribir su archivo de entrada, y el resto del
        # flujo (fallback + copyfile) asume origen != destino
        raise ValueError("Elige un archivo de destino distinto del original.")

    src_size = Path(input_path).stat().st_size
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        pdf = Pdf.open(input_path)
    except pikepdf.PasswordError as exc:
        raise ValueError("El PDF esta protegido con contrasena; "
                         "quita la proteccion primero.") from exc
    try:
        # conservar el cifrado/permisos de PDFs solo-propietario (abren sin
        # contrasena pero estan cifrados: sin esto la proteccion se perderia)
        enc = pikepdf.Encryption.copy_from(pdf) if pdf.is_encrypted else False
    except AttributeError:
        enc = True if pdf.is_encrypted else False
    try:
        for page in pdf.pages:
            try:
                # get_images: page.images esta deprecado y ademas NO ve las
                # imagenes anidadas en Form XObjects (membretes, sellos...)
                images = page.get_images() if hasattr(page, "get_images") else page.images
            except Exception:  # noqa: BLE001
                continue
            for _name, obj in list(images.items()):
                try:
                    _recompress_image(obj, quality, min_image_bytes, Name, PdfImage,
                                      max_side=max_side)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Imagen omitida al comprimir: %s", exc)
        pdf.save(output_path, compress_streams=True, encryption=enc,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate)
    finally:
        pdf.close()

    out_size = Path(output_path).stat().st_size
    if out_size >= src_size:
        # No mejoro: guarda solo con compresion de streams (sin tocar imagenes).
        pdf2 = pikepdf.Pdf.open(input_path)
        try:
            enc2 = True if pdf2.is_encrypted else False
            pdf2.save(output_path, compress_streams=True, encryption=enc2,
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


def _recompress_image(obj, quality: int, min_bytes: int, Name, PdfImage,
                      max_side: int | None = None) -> None:
    raw = bytes(obj.read_raw_bytes()) if hasattr(obj, "read_raw_bytes") else b""
    if raw and len(raw) < min_bytes:
        return  # imagen pequena: no merece la pena (y reduce riesgo)
    if "/SMask" in obj:
        # imagen con TRANSPARENCIA (logos, firmas, sellos): as_pil_image solo
        # devuelve la base, y reescribirla borrando el SMask convierte las
        # zonas transparentes en un rectangulo opaco. Se deja intacta.
        return
    pimg = PdfImage(obj)
    pil = pimg.as_pil_image()
    if pil.mode == "CMYK":
        # JPEG CMYK: PIL y el visor PDF discrepan sobre la inversion Adobe y la
        # conversion a RGB cambia los colores drasticamente. Se deja intacta.
        return
    gray = pil.mode in ("L", "1")
    if pil.mode in ("RGBA", "LA", "P"):
        pil = pil.convert("RGB")
    pil = pil.convert("L" if gray else "RGB")
    if max_side and max(pil.size) > max_side:
        # remuestrear a la resolucion del nivel: es donde esta el ahorro real
        from PIL import Image
        escala = max_side / max(pil.size)
        pil = pil.resize((max(1, round(pil.width * escala)),
                          max(1, round(pil.height * escala))), Image.LANCZOS)
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality, optimize=True)
    obj.write(buf.getvalue(), filter=Name("/DCTDecode"))
    # el XObject debe declarar las dimensiones reales de la imagen escrita
    obj.Width = pil.width
    obj.Height = pil.height
    obj.ColorSpace = Name("/DeviceGray") if gray else Name("/DeviceRGB")
    obj.BitsPerComponent = 8
    for key in ("/Decode", "/DecodeParms"):
        if key in obj:
            del obj[key]
