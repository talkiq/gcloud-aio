from typing import Any, Dict, Literal, List, Optional, Union

TYPES = Literal[
    "TYPE_UNSPECIFIED",
    "FACE_DETECTION",
    "LANDMARK_DETECTION",
    "LOGO_DETECTION",
    "LABEL_DETECTION",
    "TEXT_DETECTION",
    "DOCUMENT_TEXT_DETECTION",
    "SAFE_SEARCH_DETECTION",
    "IMAGE_PROPERTIES",
    "CROP_HINTS",
    "WEB_DETECTION",
    "PRODUCT_SEARCH",
    "OBJECT_LOCALIZATION",
]

MODELS = Literal["builtin/stable", "builtin/latest"]


# https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageRequest#imagesource
class ImageSource:
    def __init__(self, imageUri: str) -> None:
        self.gcsImageUri: Union[str, None] = None
        self.imageUri: str = imageUri

    def to_dict(self) -> Dict[str, str]:
        return {"gcsImageUri": self.gcsImageUri, "imageUri": self.imageUri}

    def from_dict(self, data: Dict, use_gcsImageUri=False) -> None:
        if use_gcsImageUri:
            self.gcsImageUri = data.get("gcsImageUri")
            self.imageUri = data.get("imageUri")
        else:
            self.gcsImageUri = None
            self.imageUri = data.get("imageUri", data.get("gcsImageUri"))


# https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageRequest#Image
class Image:
    def __init__(
        self,
        content: Optional[bytes] = None,
        source: Optional[str, ImageSource] = None,
    ) -> None:
        self.content: bytes = content
        self.source: ImageSource = source if isinstance(
            source, ImageSource
        ) else ImageSource(source)

    def to_dict(self) -> Dict[str, str]:
        return {
            "content": self.content.encode("ascii"),
            "source": self.source.to_dict(),
        }

    def from_dict(self, data: Dict) -> None:
        self.content: bytes = data.get("content").encode("ascii") if data.get(
            "content"
        ) else None
        self.source: ImageSource = ImageSource.from_dict(data.get("source", {}))


# https://cloud.google.com/vision/docs/reference/rest/v1/Feature
class Feature:
    def __init__(
        self,
        max_results: int = 50,
        feature_type: TYPES = "TYPE_UNSPECIFIED",
        model: MODELS = "builtin/stable",
    ) -> None:
        self.feature_type = feature_type
        self.max_results = max_results
        self.model = model

    @property
    def maxResults(self) -> int:
        return self.max_results

    @property
    def model(self) -> int:
        return self.model

    def to_dict(self) -> Dict[str, str]:
        return {
            "type": self.feature_type,
            "maxResults": self.maxResults,
            "model": self.model,
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/LatLng
class LatLng:
    def __init__(
        self, latitude: Union[int, float], longitude: Union[int, float]
    ) -> None:
        self.latitude = float(latitude)
        assert -90.0 < self.latitude < 90.0
        self.longitude = float(longitude)
        assert -180.0 < self.latitude < 180.0

    def to_dict(self) -> Dict[str, str]:
        return {"latitude": self.latitude, "longitude": self.longitude}


# https://cloud.google.com/vision/docs/reference/rest/v1/ImageContext#LatLongRect
class LatLongRect:
    def __init__(self, min_lat_lng: LatLng, max_lat_lng: LatLng) -> None:
        self.min_lat_lng = min_lat_lng
        self.max_lat_lng = max_lat_lng

    def to_dict(self) -> Dict[str, str]:
        return {
            "minLatLng": self.min_lat_lng.to_dict(),
            "maxLatLng": self.max_lat_lng.to_dict(),
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/ImageContext#CropHintsParams
class CropHintsParams:
    def __init__(self, aspect_ratios: List[float],) -> None:
        self.aspect_ratios = aspect_ratios

    def to_dict(self) -> Dict[str, bool]:
        return {
            "aspectRatios": self.aspect_ratios,
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/projects.locations.products.referenceImages#Vertex
class Vertex:
    def __init__(self, x: Union[int, float], y: Union[int, float]) -> None:
        self.x = float(x)
        self.y = float(y)

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y}


# https://cloud.google.com/vision/docs/reference/rest/v1/projects.locations.products.referenceImages#NormalizedVertex
class NormalizedVertex(Vertex):
    pass


# https://cloud.google.com/vision/docs/reference/rest/v1/projects.locations.products.referenceImages#BoundingPoly
class BoundingPoly:
    def __init__(
        self, vertices: List[Vertex], normalized_vertices: List[NormalizedVertex]
    ) -> None:
        self.vertices = vertices
        self.normalized_vertices = normalized_vertices

    def to_dict(self) -> Dict[str, List[Dict[str, float]]]:
        return {
            "vertices": [x.to_dict() for x in self.vertices],
            "normalizedVertices": [x.to_dict() for x in self.normalized_vertices],
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/projects.locations.productSets#ProductSet
class ProductSet:
    def __init__(self, name: str, display_name: str) -> None:
        self.name = name
        self.display_name = display_name

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "displayName": self.display_name,
        }

    def __str__(self) -> str:
        self.display_name


# https://cloud.google.com/vision/docs/reference/rest/v1/ImageContext#ProductSearchParams
class ProductSearchParams:
    def __init__(
        self,
        bounding_poly: BoundingPoly,
        product_set: ProductSet,
        product_categories: List[str],
        filter: str,
    ) -> None:
        self.bounding_poly = bounding_poly
        self.product_set = product_set
        self.product_categories = product_categories
        self.filter = filter

    def to_dict(self) -> Dict[str, str]:
        return {
            "boundingPoly": self.bounding_poly.to_dict(),
            "productSet": self.product_set.name,
            "productCategories": self.productCategories,
            "filter": self.filter,
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/ImageContext#WebDetectionParams
class WebDetectionParams:
    def __init__(self, include_geo_results: bool,) -> None:
        self.include_geo_results = include_geo_results

    def to_dict(self) -> Dict[str, bool]:
        return {
            "includeGeoResults": self.include_geo_results,
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/ImageContext
class ImageContext:
    def __init__(
        self,
        lat_long_rect: LatLongRect = None,
        language_hints: List[str] = None,
        crop_hints: CropHintsParams = None,
        product_search: ProductSearchParams = None,
        web_detection: WebDetectionParams = None,
    ) -> None:
        self.lat_long_rect = lat_long_rect
        self.language_hints = language_hints
        self.crop_hints = crop_hints
        self.product_search = product_search
        self.web_detection = web_detection

    def to_dict(self) -> Dict[str, str]:
        return {
            "latLongRect": self.lat_long_rect.to_dict(),
            "languageHints": self.language_hints,
            "cropHintsParams": self.crop_hints.to_dict(),
            "productSearchParams": self.product_search.to_dict(),
            "webDetectionParams": self.web_detection.to_dict(),
        }


# https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageRequest
class AnnotateImageRequest:
    def __init__(
        self, image: Image, features: List[Feature], image_context: ImageContext
    ) -> None:
        self.image = image
        self.features = features
        self.image_context = image_context

    def to_dict(self) -> Dict:
        return {
            "image": self.image.to_dict(),
            "features": [feature.to_dict() for feature in self.features],
            "imageContext": self.image_context.to_dict(),
        }
