from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import mss
import mss.tools
from screeninfo import get_monitors


class MonitorError(Exception):
    pass


@dataclass
class MonitorInfo:
    index: int
    x: int
    y: int
    width: int
    height: int
    is_primary: bool


class ScreenCapture:
    def list_monitors(self) -> list[MonitorInfo]:
        try:
            monitors = get_monitors()
        except Exception as exc:  # noqa: BLE001
            raise MonitorError(f"Unable to detect monitors: {exc}") from exc

        if not monitors:
            raise MonitorError("No monitors were detected.")

        return [
            MonitorInfo(
                index=index,
                x=monitor.x,
                y=monitor.y,
                width=monitor.width,
                height=monitor.height,
                is_primary=getattr(monitor, "is_primary", False),
            )
            for index, monitor in enumerate(monitors, start=1)
        ]

    def capture_monitor(self, monitor: MonitorInfo, output_path: Path) -> None:
        monitor_region = {
            "left": monitor.x,
            "top": monitor.y,
            "width": monitor.width,
            "height": monitor.height,
        }

        with mss.mss() as sct:
            image = sct.grab(monitor_region)
            mss.tools.to_png(image.rgb, image.size, output=str(output_path))
