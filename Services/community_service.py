"""Validation and private image normalization for community features."""

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_PHOTO_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
ALLOWED_IMAGE_TYPES = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


class CommunityValidationError(ValueError):
    pass


def clean_text(value, limit, label, required=False):
    value = (value or "").strip()
    if required and not value:
        raise CommunityValidationError(f"{label} je obvezno.")
    if len(value) > limit:
        raise CommunityValidationError(f"{label} je lahko dolg največ {limit} znakov.")
    return value


def normalize_photo(upload):
    if not upload or not upload.file:
        raise CommunityValidationError("Izberi fotografijo.")
    declared = (upload.content_type or "").split(";", 1)[0].lower()
    expected = ALLOWED_IMAGE_TYPES.get(declared)
    if expected is None:
        raise CommunityValidationError("Dovoljene so fotografije JPEG, PNG in WebP.")
    raw = upload.file.read(MAX_PHOTO_BYTES + 1)
    if not raw or len(raw) > MAX_PHOTO_BYTES:
        raise CommunityValidationError("Fotografija mora biti manjša od 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as probe:
                if probe.format != expected or probe.width * probe.height > MAX_IMAGE_PIXELS:
                    raise CommunityValidationError("Vsebina ali velikost fotografije ni dovoljena.")
                probe.verify()
            with Image.open(io.BytesIO(raw)) as image:
                image = ImageOps.exif_transpose(image)
                image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                    alpha = image.convert("RGBA")
                    flattened = Image.new("RGB", alpha.size, "white")
                    flattened.paste(alpha, mask=alpha.getchannel("A"))
                    image = flattened
                else:
                    image = image.convert("RGB")
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=85, optimize=True)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        if isinstance(exc, CommunityValidationError):
            raise
        raise CommunityValidationError("Fotografije ni mogoče varno obdelati.") from exc
