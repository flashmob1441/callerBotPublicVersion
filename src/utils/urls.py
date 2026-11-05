from urllib.parse import urlparse

# Источник определяется по hostname, а не по подстроке: 'evil.com/?tiktok.com' не должен проходить.
SOURCE_HOSTS = {
    'tiktok': ('tiktok.com',),
    'instagram': ('instagram.com',),
    'youtube': ('youtube.com',),
    'rednote': ('xhslink.com',),
}


def get_source(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    for source, domains in SOURCE_HOSTS.items():
        if any(host == d or host.endswith('.' + d) for d in domains):
            if source == 'youtube' and not parsed.path.startswith('/shorts/'):
                return None
            return source
    return None
