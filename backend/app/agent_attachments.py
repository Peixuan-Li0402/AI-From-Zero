from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .config import settings
from .pdf import extract_pdf_pages


class AttachmentError(ValueError):
    pass


@dataclass(slots=True)
class AttachmentInput:
    kind: str
    url: str = ""
    filename: str = ""
    format: str = ""


@dataclass(slots=True)
class ProcessedDocument:
    url: str
    filename: str
    text: str = ""
    pages: list[dict] = field(default_factory=list)
    structure: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


_CACHE: OrderedDict[str, tuple[float, ProcessedDocument]] = OrderedDict()
_CACHE_TTL = 15 * 60
_CACHE_LIMIT = 16


def _safe_filename(value: str, fallback: str = "document") -> str:
    name = Path((value or "").replace("\\", "/")).name
    name = "".join(char for char in name if ord(char) >= 32 and char not in {'"', "<", ">", "|"})
    return name[:180] or fallback


def _host_allowed(hostname: str) -> bool:
    allowed = settings.qxd_attachment_allowed_hosts
    if not allowed:
        return True
    host = hostname.lower().rstrip(".")
    return any(host == item.lower().lstrip(".") or host.endswith("." + item.lower().lstrip(".")) for item in allowed)


def _resolve_host_sync(hostname: str, port: int) -> set[str]:
    return {item[4][0] for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)}


async def _resolve_host(hostname: str, port: int) -> set[str]:
    try:
        return await asyncio.to_thread(_resolve_host_sync, hostname, port)
    except socket.gaierror as exc:
        raise AttachmentError("附件地址无法解析") from exc


def _ensure_public_addresses(addresses: set[str], *, allow_private_proxy: bool = False) -> None:
    if not addresses:
        raise AttachmentError("附件地址没有可用的网络地址")
    for raw in addresses:
        try:
            address = ipaddress.ip_address(raw.split("%", 1)[0])
        except ValueError as exc:
            raise AttachmentError("附件地址解析结果无效") from exc
        if not address.is_global and not allow_private_proxy:
            raise AttachmentError("附件地址指向本机或私有网络，已拒绝访问")


async def validate_public_url(url: str) -> tuple[str, set[str]]:
    if not url or url.lower().startswith("data:"):
        raise AttachmentError("附件必须使用可下载的 HTTP/HTTPS URL，不能使用 Base64")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise AttachmentError("附件 URL 只支持 HTTP 或 HTTPS")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".localhost") or not _host_allowed(hostname):
        raise AttachmentError("附件域名不在允许范围内")
    try:
        literal_address = ipaddress.ip_address(hostname.split("%", 1)[0])
    except ValueError:
        literal_address = None
    if literal_address is not None and not literal_address.is_global:
        raise AttachmentError("附件 URL 不能直接使用本机或私有网络 IP")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = await _resolve_host(hostname, port)
    _ensure_public_addresses(addresses, allow_private_proxy=settings.qxd_allow_private_dns_proxy)
    return hostname, addresses


def _cache_get(url: str) -> ProcessedDocument | None:
    cached = _CACHE.get(url)
    if not cached:
        return None
    expires_at, document = cached
    if expires_at <= time.monotonic():
        _CACHE.pop(url, None)
        return None
    _CACHE.move_to_end(url)
    return document


def _cache_put(url: str, document: ProcessedDocument) -> None:
    _CACHE[url] = (time.monotonic() + _CACHE_TTL, document)
    _CACHE.move_to_end(url)
    while len(_CACHE) > _CACHE_LIMIT:
        _CACHE.popitem(last=False)


async def download_url(url: str) -> tuple[bytes, str, str]:
    max_bytes = settings.qxd_max_attachment_mb * 1024 * 1024
    timeout = httpx.Timeout(connect=5.0, read=25.0, write=5.0, pool=5.0)
    current = url
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,
        trust_env=settings.qxd_allow_private_dns_proxy,
    ) as client:
        for redirect_count in range(4):
            hostname, _addresses_before = await validate_public_url(current)
            async with client.stream("GET", current, headers={"User-Agent": "AI-From-Zero-Agent/1.0"}) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location", "")
                    if not location or redirect_count >= 3:
                        raise AttachmentError("附件下载重定向次数过多")
                    current = urljoin(current, location)
                    continue
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    raise AttachmentError(f"附件下载失败（HTTP {response.status_code}）") from exc
                raw_length = response.headers.get("content-length", "")
                if raw_length.isdigit() and int(raw_length) > max_bytes:
                    raise AttachmentError(f"附件超过 {settings.qxd_max_attachment_mb}MB 限制")
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise AttachmentError(f"附件超过 {settings.qxd_max_attachment_mb}MB 限制")
                    chunks.append(chunk)
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                disposition = response.headers.get("content-disposition", "")
            parsed = urlparse(current)
            addresses_after = await _resolve_host(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            _ensure_public_addresses(addresses_after, allow_private_proxy=settings.qxd_allow_private_dns_proxy)
            filename = _safe_filename(unquote(Path(parsed.path).name), "document")
            disposition_name = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, re.IGNORECASE)
            if disposition_name:
                filename = _safe_filename(unquote(disposition_name.group(1).strip()), filename)
            return b"".join(chunks), content_type, filename
    raise AttachmentError("附件下载失败")


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AttachmentError("文本附件不是可识别的 UTF-8 或中文编码")


async def process_document(item: AttachmentInput) -> ProcessedDocument:
    if not item.url:
        raise AttachmentError("清小搭只提供了 file_id，当前服务需要可下载的 file.url")
    cached = _cache_get(item.url)
    if cached:
        return cached

    content, content_type, downloaded_name = await download_url(item.url)
    filename = _safe_filename(item.filename, downloaded_name)
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        try:
            extracted = await asyncio.to_thread(extract_pdf_pages, content)
        except Exception as exc:
            raise AttachmentError(f"PDF 解析失败：{exc}") from exc
        if len(extracted.get("text", "").strip()) < 50:
            raise AttachmentError("PDF 没有可提取文字，可能是扫描版；请改发文本型 PDF")
        document = ProcessedDocument(
            url=item.url,
            filename=filename if filename.lower().endswith(".pdf") else f"{filename}.pdf",
            text=extracted["text"],
            pages=extracted.get("pages", []),
            structure=extracted.get("structure", {}),
            warnings=extracted.get("warnings", []),
        )
    elif content_type == "text/html" or suffix in {".html", ".htm"}:
        html = _decode_text(content)
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True)).strip()
        if len(text) < 50:
            raise AttachmentError("论文网页没有可提取的正文")
        document = ProcessedDocument(url=item.url, filename=filename, text=text)
    elif suffix in {".txt", ".md", ".markdown"} or content_type.startswith("text/"):
        text = _decode_text(content).strip()
        if not text:
            raise AttachmentError("文本附件为空")
        document = ProcessedDocument(url=item.url, filename=filename, text=text)
    else:
        raise AttachmentError("当前可读取 PDF、TXT 和 Markdown；其他文件类型已忽略")
    _cache_put(item.url, document)
    return document
