from rest_framework.response import Response

class StandardResponseMixin:
    """Mixin for consistent API responses"""

    def success_response(self, data, message="Success", status_code=200):
        return Response({
            "success": True,
            "statusCode": status_code,
            "message": message,
            "data": data,
            # "timestamp": timezone.now().isoformat()
        }, status=status_code)

    def error_response(self, message, status_code=400, data=None):
        detail = self._extract_error_detail(data)
        if detail and detail not in message:
            message = f"{message}: {detail}"
        return Response({
            "success": False,
            "statusCode": status_code,
            "message": message,
            "data": data,
            # "timestamp": timezone.now().isoformat()
        }, status=status_code)

    def _extract_error_detail(self, data):
        if not data:
            return None
        if isinstance(data, str):
            return data
        if isinstance(data, list) and data:
            return self._extract_error_detail(data[0])
        if isinstance(data, dict):
            if "non_field_errors" in data:
                return self._extract_error_detail(data["non_field_errors"])
            for value in data.values():
                detail = self._extract_error_detail(value)
                if detail:
                    return detail
        return None
