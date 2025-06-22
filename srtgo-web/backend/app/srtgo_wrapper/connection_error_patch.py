"""
Patch for curl_cffi ConnectionError compatibility
"""
import sys

# First, check what's available in curl_cffi.requests.exceptions
import curl_cffi.requests.exceptions

# If ConnectionError doesn't exist, create it from the base RequestsError
if not hasattr(curl_cffi.requests.exceptions, 'ConnectionError'):
    # Use the base RequestsError or create a custom exception
    class ConnectionError(curl_cffi.requests.exceptions.RequestsError):
        """A Connection error occurred."""
        pass
    
    # Add it to the module
    curl_cffi.requests.exceptions.ConnectionError = ConnectionError
    
    # Also add it to sys.modules for import compatibility
    sys.modules['curl_cffi.requests.exceptions'].ConnectionError = ConnectionError