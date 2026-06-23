from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx
from azure.identity import DefaultAzureCredential


@dataclass(slots=True)
class ModelConfig:
    alias: str
    base_url: str
    api_path: str
    api_version: str
    model: str
    api_key: str
    auth_mode: str


def _prefix(alias: str) -> str:
    return f"MODEL_{alias.upper().replace('-', '_')}_"


def load_model_config(alias: str) -> ModelConfig:
    prefix = _prefix(alias)
    return ModelConfig(
        alias=alias,
        base_url=os.getenv(f'{prefix}BASE_URL', '').rstrip('/'),
        api_path=os.getenv(f'{prefix}API_PATH', '/chat/completions'),
        api_version=os.getenv(f'{prefix}API_VERSION', '2024-05-01-preview'),
        model=os.getenv(f'{prefix}MODEL', alias),
        api_key=os.getenv(f'{prefix}API_KEY', ''),
        auth_mode=os.getenv(f'{prefix}AUTH_MODE', 'bearer').lower(),
    )


def _auth_headers(cfg: ModelConfig) -> dict[str, str]:
    """Build auth headers; supports API key or Entra ID token."""
    if cfg.auth_mode == 'api-key':
        return {'api-key': cfg.api_key}
    
    if cfg.auth_mode == 'entra-id' or (not cfg.api_key and cfg.auth_mode == 'bearer'):
        try:
            credential = DefaultAzureCredential()
            token = credential.get_token('https://cognitiveservices.azure.com/.default')
            return {'Authorization': f'Bearer {token.token}'}
        except Exception as e:
            raise ValueError(f'Failed to acquire Entra ID token: {e}')
    
    return {'Authorization': f'Bearer {cfg.api_key}'}


async def chat_completion(
    cfg: ModelConfig,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: int,
) -> tuple[str, int]:
    if not cfg.base_url:
        raise ValueError(f'Model config incomplete for alias: {cfg.alias}')

    url = f'{cfg.base_url}{cfg.api_path}'
    payload = {
        'model': cfg.model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    params = {'api-version': cfg.api_version} if cfg.api_version else None

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        response = await client.post(url, json=payload, params=params, headers=_auth_headers(cfg))
        response.raise_for_status()
        body = response.json()

    latency_ms = int((time.perf_counter() - start) * 1000)
    content = body.get('choices', [{}])[0].get('message', {}).get('content', '')
    if not content:
        content = str(body)
    return content, latency_ms
