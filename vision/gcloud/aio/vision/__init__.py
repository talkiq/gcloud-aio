from pkg_resources import get_distribution

__version__ = get_distribution("gcloud-aio-vision").version

from gcloud.aio.vision.vision import Vision
from gcloud.aio.vision.types import (
    AnnotateImageRequest,
    BoundingPoly,
    CropHintsParams,
    Feature,
    Image,
    ImageContext,
    LatLng,
    LatLongRect,
    NormalizedVertex,
    ProductSearchParams,
    ProductSet,
    Vertex,
    WebDetectionParams,
)


__all__ = [
    "__version__",
    "AnnotateImageRequest",
    "BoundingPoly",
    "CropHintsParams",
    "Feature",
    "Image",
    "ImageContext",
    "LatLng",
    "LatLongRect",
    "NormalizedVertex",
    "ProductSearchParams",
    "ProductSet",
    "Vertex",
    "Vision" "WebDetectionParams",
]
