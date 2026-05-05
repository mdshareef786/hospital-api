from typing import Any
import math


def success_response(message: str, data: Any = None):
    return {
        "success": True,
        "message": message,
        "data": data,
        "errors": None
    }


def error_response(message: str, errors: Any = None):
    return {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors
    }


def paginated_response(message: str, items: list, total: int, page: int, page_size: int):
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size else 1
        },
        "errors": None
    }