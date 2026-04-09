from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import platform


@dataclass(frozen=True)
class PlatformProfile:
    system: str
    release: str
    machine: str
    cpu_cores: int
    supports_host_ids: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def detect_platform() -> PlatformProfile:
    system = platform.system().lower()
    return PlatformProfile(
        system=system,
        release=platform.release(),
        machine=platform.machine().lower(),
        cpu_cores=os.cpu_count() or 1,
        supports_host_ids=(system == "linux"),
    )
