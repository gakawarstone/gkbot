import re


def get_vk_id(url: str) -> str:
    """Extract VK identifier from URL."""
    if url.startswith("https://vk.cc/"):
        return url

    match = re.search(r"(wall-\d+|video-\d+_\d+)", url)
    if match:
        return match.group(1)

    return url


def reconstruct_vk_url(vk_id: str) -> str:
    """Reconstruct full VK URL from identifier."""
    if vk_id.startswith("http"):
        return vk_id
    return f"https://vk.com/{vk_id}"
