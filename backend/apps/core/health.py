"""
Health check views for monitoring.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis


def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if service is healthy.
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "cache": "unknown"
    }
    
    # Check database
    try:
        connection.ensure_connection()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status["cache"] = "connected"
        else:
            health_status["cache"] = "error: value mismatch"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["cache"] = f"error: {str(e)}"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check for load balancers.
    Returns 200 when ready to accept traffic.
    """
    return JsonResponse({"status": "ready"})


def liveness_check(request):
    """
    Liveness check for container orchestrators.
    Returns 200 if application is running.
    """
    return JsonResponse({"status": "alive"})
