import json
import socket
from urllib.parse import urlparse

import requests
from fastapi import HTTPException


def check_service(url: str, name: str):
    try:
        response = requests.get(url, timeout=3)
        print(f"Health check for {name} service at {url} returned status code {response.status_code}")
        if response.status_code < 400:
            return f"{name} service is reachable at {url}"
        if response.status_code >= 400:
            raise HTTPException(
                status_code=503,
                detail=f"{name} service is not healthy at {url}"
            )
    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=503,
            detail=f"{name} service is not reachable at {url}"
        )
    

def ensure_interface_manager_port_running(
    config_path: str,
    timeout: float = 1.5
):
    # 1️⃣ Read config.json
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read Interface Manager config: {str(e)}"
        )

    # 2️⃣ Extract base_url
    base_url = config.get("base_url")
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="base_url missing in Interface Manager config"
        )

    # 3️⃣ Parse host & port
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port

    if not host or not port:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid base_url in Interface Manager config: {base_url}"
        )

    # 4️⃣ TCP port check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        result = sock.connect_ex((host, port))
        if result != 0:
            raise HTTPException(
                status_code=503,
                detail=f"Interface Manager is not running at {host}:{port}"
            )
    finally:
        sock.close()    