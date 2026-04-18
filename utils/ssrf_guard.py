import ipaddress
import socket
from pydantic import HttpUrl

# All IP ranges that must never receive outbound webhook requests.
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # RFC-1918 private
    ipaddress.ip_network("172.16.0.0/12"),     # RFC-1918 private
    ipaddress.ip_network("192.168.0.0/16"),    # RFC-1918 private
    ipaddress.ip_network("169.254.0.0/16"),    # link-local / cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),     # shared address space (RFC-6598)
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
    ipaddress.ip_network("192.0.0.0/24"),      # IETF protocol assignments
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


def _is_blocked(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparseable → block
    return any(addr in net for net in _BLOCKED_NETWORKS)


def assert_public_url(url: HttpUrl) -> HttpUrl:
    """
    Raises ValueError if the URL resolves to a private/reserved IP address.
    Called as a Pydantic AfterValidator on webhook_url fields.
    """
    host = url.host
    if not host:
        raise ValueError("Webhook URL has no host")

    try:
        results = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"Webhook URL host could not be resolved: {exc}") from exc

    for _family, _type, _proto, _canonname, sockaddr in results:
        ip = sockaddr[0]
        if _is_blocked(ip):
            raise ValueError(
                f"Webhook URL resolves to a private or reserved address ({ip}) "
                "and is not allowed"
            )

    return url
