from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    def fits(self, width: int, height: int) -> bool:
        return width <= self.width and height <= self.height

    def intersects(self, other: "Rect") -> bool:
        return not (
            other.x >= self.x2
            or other.x2 <= self.x
            or other.y >= self.y2
            or other.y2 <= self.y
        )


class PackingAlgorithm:
    def add(self, width: int, height: int) -> Tuple[int, Rect]:
        """Place a rectangle (width, height). Returns (page_index, Rect)."""
        raise NotImplementedError

    @property
    def page_count(self) -> int:
        raise NotImplementedError


class MaxRectsAlgorithm(PackingAlgorithm):
    """MaxRects with best short-side fit heuristic."""

    def __init__(self, page_width: int, page_height: int, max_pages: Optional[int] = None) -> None:
        self.page_width = page_width
        self.page_height = page_height
        self.max_pages = max_pages
        self._pages: List[_Page] = [self._new_page()]

    @property
    def page_count(self) -> int:
        return len(self._pages)

    def add(self, width: int, height: int) -> Tuple[int, Rect]:
        if width > self.page_width or height > self.page_height:
            raise ValueError(f"Rect {width}x{height} exceeds page size {self.page_width}x{self.page_height}")

        best_page, placement = self._find_page_and_position(width, height)
        if placement is None or best_page is None:
            # allocate new page and retry once
            if self.max_pages is not None and len(self._pages) >= self.max_pages:
                raise ValueError(f"No space left: reached max pages ({self.max_pages})")
            self._pages.append(self._new_page())
            best_page = len(self._pages) - 1
            placement, _, _ = self._find_position_on_page(self._pages[-1], width, height)

        if placement is None or best_page is None:
            raise ValueError(f"Could not place rect {width}x{height}")

        self._place_rect(self._pages[best_page], placement)
        return best_page, placement

    # Internals --------------------------------------------------------------
    def _find_page_and_position(self, width: int, height: int) -> Tuple[Optional[int], Optional[Rect]]:
        best: Tuple[Optional[int], Optional[Rect]] = (None, None)
        best_short = 1_000_000_000
        best_long = 1_000_000_000
        for idx, page in enumerate(self._pages):
            rect, short_fit, long_fit = self._find_position_on_page(page, width, height)
            if rect and (short_fit < best_short or (short_fit == best_short and long_fit < best_long)):
                best = (idx, rect)
                best_short = short_fit
                best_long = long_fit
        return best

    def _find_position_on_page(
        self, page: "_Page", width: int, height: int
    ) -> Tuple[Optional[Rect], int, int]:
        best_rect: Optional[Rect] = None
        best_short = 1_000_000_000
        best_long = 1_000_000_000
        for free in page.free_rects:
            if free.fits(width, height):
                leftover_h = abs(free.height - height)
                leftover_w = abs(free.width - width)
                short_fit = min(leftover_w, leftover_h)
                long_fit = max(leftover_w, leftover_h)
                if short_fit < best_short or (short_fit == best_short and long_fit < best_long):
                    best_rect = Rect(free.x, free.y, width, height)
                    best_short = short_fit
                    best_long = long_fit
            if free.fits(height, width):
                leftover_h = abs(free.height - width)
                leftover_w = abs(free.width - height)
                short_fit = min(leftover_w, leftover_h)
                long_fit = max(leftover_w, leftover_h)
                if short_fit < best_short or (short_fit == best_short and long_fit < best_long):
                    best_rect = Rect(free.x, free.y, height, width)
                    best_short = short_fit
                    best_long = long_fit
        return best_rect, best_short, best_long

    def _place_rect(self, page: "_Page", used: Rect) -> None:
        i = 0
        while i < len(page.free_rects):
            if self._split_free_node(page, page.free_rects[i], used):
                page.free_rects.pop(i)
                continue
            i += 1
        self._prune_free_list(page)

    def _split_free_node(self, page: "_Page", free: Rect, used: Rect) -> bool:
        if not free.intersects(used):
            return False

        if used.x > free.x and used.x < free.x2:
            page.free_rects.append(Rect(free.x, free.y, used.x - free.x, free.height))
        if used.x2 < free.x2:
            page.free_rects.append(Rect(used.x2, free.y, free.x2 - used.x2, free.height))
        if used.y > free.y and used.y < free.y2:
            page.free_rects.append(Rect(free.x, free.y, free.width, used.y - free.y))
        if used.y2 < free.y2:
            page.free_rects.append(Rect(free.x, used.y2, free.width, free.y2 - used.y2))

        return True

    def _prune_free_list(self, page: "_Page") -> None:
        i = 0
        while i < len(page.free_rects):
            j = i + 1
            removed = False
            while j < len(page.free_rects):
                if self._is_contained_in(page.free_rects[i], page.free_rects[j]):
                    page.free_rects.pop(i)
                    removed = True
                    break
                if self._is_contained_in(page.free_rects[j], page.free_rects[i]):
                    page.free_rects.pop(j)
                    continue
                j += 1
            if not removed:
                i += 1

    @staticmethod
    def _is_contained_in(a: Rect, b: Rect) -> bool:
        return a.x >= b.x and a.y >= b.y and a.x2 <= b.x2 and a.y2 <= b.y2

    def _new_page(self) -> "_Page":
        return _Page(free_rects=[Rect(0, 0, self.page_width, self.page_height)])


@dataclass
class _Page:
    free_rects: List[Rect]
