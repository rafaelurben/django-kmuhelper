"""Useful constants for api views"""

from django.http import JsonResponse

APIKEY_INVALID = JsonResponse({
    "error": "apikey-invalid",
    "message": "Your api key is invalid!"
}, status=403)

ENDPOINT_NOT_FOUND = JsonResponse({
    "error": "endpoint-not-found",
    "message": "This endpoint does not exist!"
}, status=404)

NO_PERMISSION_APIKEY = JsonResponse({
    "error": "no-permission",
    "message": "You don't have permission to access this endpoint! (authentication method: api key)"
}, status=403)

NO_PERMISSION_SESSION = JsonResponse({
    "error": "no-permission",
    "message": "You don't have permission to access this endpoint! (authentication method: session)"
}, status=403)

NOT_AUTHENTICATED = JsonResponse({
    "error": "not-authenticated",
    "message": "You must authenticate yourself to use this endpoint!"
}, status=401)

OBJ_NOT_FOUND = JsonResponse({
    "error": "object-not-found",
    "message": "The object couln't be found!",
}, status=400)

SUCCESSFULLY_CHANGED = JsonResponse({
    "success": "change-successfull",
    "message": "Successfully changed object!"
}, status=200)
