"""
Lightweight, shared memory instrumentation for logmerger phases.

Phases:
- Merge phase: littletable.Table.insert_many in LogMergerApplication.run()
- Display phase: all allocations inside InteractiveLogMergeViewerApp.load_data_side_by_side()

This module centralizes tracemalloc control, phase peak tracking, optional
snapshots, and an end-of-program summary printout.
"""

from __future__ import annotations

import atexit
import os
import tracemalloc
from typing import Optional


class _MemStats:
    def __init__(self) -> None:
        self.enabled: bool = False
        self.started: bool = False
        self.merge_peak: int = 0  # bytes
        self.display_peak: int = 0  # bytes
        self.total_peak: int = 0  # bytes

        # snapshots (optional, for short-term diagnostics)
        self._snapshots_enabled: bool = (
            os.getenv("LOGMERGER_MEM_SNAPSHOTS", "1").lower() not in {"0", "false", "off"}
        )
        self.merge_snapshot = None
        self.display_snapshot = None

    # --- lifecycle ---
    def ensure_started(self) -> None:
        if not self.started:
            tracemalloc.start()
            self.started = True
            self.enabled = True

    # --- sampling ---
    def _sample_into(self, which: str) -> None:
        if not self.enabled:
            return
        _, peak = tracemalloc.get_traced_memory()
        if which == "merge" and peak > self.merge_peak:
            self.merge_peak = peak
        elif which == "display" and peak > self.display_peak:
            self.display_peak = peak
        if peak > self.total_peak:
            self.total_peak = peak

    def sample_merge(self) -> None:
        self._sample_into("merge")

    def sample_display(self) -> None:
        self._sample_into("display")

    # --- snapshots for top-allocator diagnostics ---
    def _snapshot_into(self, which: str) -> None:
        if not (self.enabled and self._snapshots_enabled):
            return
        try:
            snap = tracemalloc.take_snapshot()
        except Exception:
            return
        if which == "merge":
            self.merge_snapshot = snap
        elif which == "display":
            self.display_snapshot = snap

    def snap_merge(self) -> None:
        self._snapshot_into("merge")

    def snap_display(self) -> None:
        self._snapshot_into("display")

    # --- reporting ---
    @staticmethod
    def _fmt_bytes(b: int) -> str:
        mb = b / (1024 * 1024)
        kb = b / 1024
        if mb >= 1:
            return f"{mb:.2f} MiB ({kb:.0f} KiB)"
        return f"{kb:.0f} KiB"

    def as_summary_lines(self) -> list[str]:
        if not self.enabled:
            return ["Memory instrumentation disabled or not used."]
        return [
            "Memory usage summary (tracemalloc):",
            f"  Phase 1 – merge rows peak: {self._fmt_bytes(self.merge_peak)}",
            f"  Phase 2 – display table peak: {self._fmt_bytes(self.display_peak)}",
            f"  Overall process peak: {self._fmt_bytes(self.total_peak)}",
        ]


GLOBAL_MEM_STATS = _MemStats()


def _format_snapshot(title: str, snap) -> list[str]:
    try:
        if not snap:
            return []
        # Prefer traces from our code and UI libs first
        filters = [
            tracemalloc.Filter(True, "*logmerger*"),
            tracemalloc.Filter(True, "*textual*"),
            tracemalloc.Filter(True, "*rich*"),
        ]
        filtered = snap.filter_traces(filters)
        snap_use = filtered if filtered.traces else snap
        stats = snap_use.statistics("traceback")
        top_n = int(os.getenv("LOGMERGER_MEM_SNAPSHOT_TOP", "12"))
        out = [f"{title} (top {top_n} by cumulative size):"]
        for i, stat in enumerate(stats[:top_n], start=1):
            size_kib = stat.size / 1024.0
            frame = stat.traceback[-1] if stat.traceback else None
            loc = f"{frame.filename}:{frame.lineno}" if frame else "<unknown>"
            out.append(f"  {i:2d}. {size_kib:8.1f} KiB at {loc}")
        return out
    except Exception:
        return []


def _print_memory_summary_at_exit() -> None:
    try:
        lines = GLOBAL_MEM_STATS.as_summary_lines()
        report_lines = ["\n=== Log Merger Memory Summary ===", *lines]
        # Include short-term top-allocator snapshots if available
        report_lines += _format_snapshot("Top allocators – merge phase", GLOBAL_MEM_STATS.merge_snapshot)
        report_lines += _format_snapshot("Top allocators – display phase", GLOBAL_MEM_STATS.display_snapshot)
        report_lines.append("=== End Memory Summary ===\n")
        print("\n".join(report_lines))
    except Exception:
        # never let exit printing crash the app
        pass


atexit.register(_print_memory_summary_at_exit)
