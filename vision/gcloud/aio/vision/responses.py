from typing import Dict
from gcloud.aio.vision import BoundingPoly


# https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageResponse#FaceAnnotation
class FaceAnnotation:
    def __init__(self, *args, **kwargs) -> None:
        self.data = kwargs

    @property
    def boundingPoly(self):
        return BoundingPoly.from_dict(self.data.get("boundingPoly"))

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**d)


# https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageResponse
class AnnotateImageResponse:
    def __init__(self, *args, **kwargs) -> None:
        self._face_annotations = kwargs.get("faceAnnotations")
        self._landmark_annotations = kwargs.get("landmarkAnnotations")
        self._logo_annotations = kwargs.get("logoAnnotations")
        self._label_annotations = kwargs.get("labelAnnotations")
        self._localized_object_annotations = kwargs.get("localizedObjectAnnotations")
        self._text_annotations = kwargs.get("textAnnotations")
        self._full_text_annotation = kwargs.get("fullTextAnnotation")
        self._safe_search_annotation = kwargs.get("safeSearchAnnotation")
        self._image_properties_annotation = kwargs.get("imagePropertiesAnnotation")
        self._crop_hints_annotation = kwargs.get("cropHintsAnnotation")
        self._web_detection = kwargs.get("webDetection")
        self._product_search_results = kwargs.get("productSearchResults")
        self._error = kwargs.get("error")
        self._context = kwargs.get("context")

    @property
    def face_annotations(self):
        return [FaceAnnotation.from_dict(x) for x in self._face_annotations]
