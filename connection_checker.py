import json 
import os 
import time 
import traceback 
import urllib.request
from urllib.parse import urlparse
import socket
import sys 
from dotenv import load_dotenv
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_TOKEN = os.getenv("OLLAMA_TOKEN")

def check_connection(host_url: str, timeout: int = 5) -> dict:
    parsed = urlparse(host_url)
    hostname = parsed.hostname or "localhost"
    port = parsed.port or 11434
    result = {
        "host": host_url,
        "hostname": hostname,
        "port": port,
        "reachable": False,
        "dns_resolved": None,
        "tcp_connected": None,
        "http_accessible": None,
        "latency_ms": None,
        "error": None
    }
    try:
        ip = socket.getaddrinfo(hostname, None)[0][4][0]
        result["dns_resolved"] = ip
    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {e}"
        return result
    
    start = time.time()
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            result["tcp_connected"] = True
            result["latency_ms"] = round((time.time() - start) * 1000, 2)
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result["tcp_connected"] = False
        result["error"] = f"TCP connection failed: {e}"
        return result
    try:
        req = urllib.request.Request(
            f"{host_url}/api/tags",
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {OLLAMA_TOKEN}"  

            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result["http_accessible"] = resp.status == 200
            result["reachable"] = True
    except Exception as e:
        result["http_accessible"] = False
        result["error"] = f"HTTP check failed: {e}"
    
    return result

def log_connection_status(conn_info: dict):
    print(f"OLLAMA CONNECTION CHECK")
    print(f"Host URL:{conn_info['host']}")
    print(f"Resolved IP:{conn_info['dns_resolved'] or 'N/A'}")
    print(f"Port:{conn_info['port']}")
    tcp_status = 'connected' if conn_info['tcp_connected'] else 'Not Connected'
    latency = f" ({conn_info['latency_ms']}ms)" if conn_info['latency_ms'] else ""
    print(f"TCP Connect:{tcp_status}{latency}")
    print(f"HTTP API:{'connected' if conn_info['http_accessible'] else 'not connected'}")
    print(f"Status:{'REACHABLE' if conn_info['reachable'] else 'UNREACHABLE'}")
    if conn_info['error']:
        print(f"Error:{conn_info['error']}")
    print("*"* 50)
    sys.stdout.flush()