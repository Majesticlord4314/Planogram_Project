"""
Mac Accessories Planogram Generator (Clean 4-row version)
- Reads products from dataset (CSV with cohort file)
- Builds 4 rows based on business rules (no hard-coded products)
- Matches row widths visually for Rows 1–3; Row 4 has exactly 3 keyboard covers centered
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import pandas as pd

# Repo root (Planogram)
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_CSV = REPO_ROOT / "data/raw/accessories/mac-accessories-transformed.csv"
COHORT_CSV = REPO_ROOT / "data/raw/cohorts/mac_planogram_cohorts.csv"
OUTPUT_DIR = REPO_ROOT / "output"

logger = logging.getLogger(__name__)


@dataclass
class MacProduct:
    product_name: str
    series: str
    category: str
    subcategory: str
    brand: str
    width: float
    height: float
    depth: float
    frequency: int
    attach_rate: float


class MacAccessoriesGenerator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # -------------------------- Data -------------------------- #
    def load_mac_data(self) -> List[MacProduct]:
        if not DATA_CSV.exists():
            raise FileNotFoundError(f"Missing Mac accessories file: {DATA_CSV}")
        if not COHORT_CSV.exists():
            raise FileNotFoundError(f"Missing Mac cohorts file: {COHORT_CSV}")

        acc = pd.read_csv(DATA_CSV)
        acc.columns = acc.columns.str.strip()
        acc = acc.apply(lambda s: s.str.strip() if s.dtype == "object" else s)

        cohorts = pd.read_csv(COHORT_CSV)
        cohorts.columns = cohorts.columns.str.strip()
        attach = {r["accessory_product"]: float(r["attach_rate"]) for _, r in cohorts.iterrows()}

        products: List[MacProduct] = []
        for _, r in acc.iterrows():
            products.append(
                MacProduct(
                    product_name=r["product_name"],
                    series=r["series"],
                    category=(r["category"] or "").strip().lower(),
                    subcategory=str(r["subcategory"]).strip(),
                    brand=str(r["brand"]).strip(),
                    width=float(r["width"]),
                    height=float(r["height"]),
                    depth=float(r["depth"]),
                    frequency=int(r["frequency"]),
                    attach_rate=float(attach.get(r["product_name"], 0.0)),
                )
            )
        # Prioritize by attach_rate * frequency
        products.sort(key=lambda p: p.attach_rate * p.frequency, reverse=True)
        return products

    # ------------------------ Helpers ------------------------- #
    @staticmethod
    def _w_h(p: MacProduct) -> Tuple[float, float]:
        """Map real dimensions to display rectangles.
        - Use width as-is
        - Use the larger of height/depth as display height (packages often have depth > height)
        - Apply category-aware scaling so privacy filters are visually larger
        """
        c = (p.category or "").lower()
        width_cm = float(p.width or 0)
        height_cm = float(max(p.height or 0, p.depth or 0))

        # Base pixel scales
        base_w = width_cm * 10.0
        base_h = height_cm * 8.0

        # Category adjustments
        if "privacy" in c:
            # Reduce earlier scaling by ~10%
            base_w *= 1.17  # was 1.30
            base_h *= 1.08  # was 1.20
        elif "keyboard" in c or c == "keyboard skin":
            # Keyboard covers: longer and slimmer
            base_w *= 1.15
            base_h *= 0.80
        elif "hub" in c:
            base_w *= 1.05
        elif "charger" in c or "power bank" in c:
            base_h *= 1.10
        elif "cable" in c:
            base_h *= 0.90

        # Final clamps (keep visual balance yet allow large privacy filters)
        w = max(90, min(420, base_w))
        h = max(80, min(240, base_h))
        return float(w), float(h)

    def _pack_row_by_width(self, candidates: List[MacProduct], target_width: float, max_items: int, spacing: int = 18) -> List[MacProduct]:
        if not candidates:
            return []
        # Sort by height desc to keep row height consistent
        dims = [(p, *self._w_h(p)) for p in candidates]
        dims.sort(key=lambda x: x[2], reverse=True)
        row: List[MacProduct] = []
        used_names: Dict[str, int] = {}
        total_w = 0.0
        for p, w, h in dims:
            if len(row) >= max_items:
                break
            if total_w + (spacing if row else 0) + w <= target_width:
                row.append(p)
                total_w += (spacing if len(row) > 1 else 0) + w
                used_names[p.product_name] = used_names.get(p.product_name, 0) + 1
        # If width still far from target, allow one round of duplicates of the best-fitting items
        i = 0
        while len(row) < max_items and i < len(dims):
            p, w, h = dims[i]
            if total_w + spacing + w <= target_width and used_names.get(p.product_name, 0) < 2:
                row.append(p)
                total_w += (spacing if len(row) > 1 else 0) + w
                used_names[p.product_name] = used_names.get(p.product_name, 0) + 1
            i += 1
        return row

    @staticmethod
    def _is_keyboard(p: MacProduct) -> bool:
        n = p.product_name.lower()
        c = (p.category or "").lower()
        return ("keyboard" in n) or ("keyboard" in c) or (c == "keyboard skin")

    @staticmethod
    def _is_privacy(p: MacProduct) -> bool:
        n = p.product_name.lower()
        c = (p.category or "").lower()
        return ("privacy" in n) or (c == "privacy filter")

    @staticmethod
    def _is_hub_like(p: MacProduct) -> bool:
        n = p.product_name.lower()
        c = (p.category or "").lower()
        return ("hub" in n) or ("dock" in n) or ("7 in 1" in n or "7-in-1" in n or "7 in1" in n or "7in1" in n) or (c == "hub")

    @staticmethod
    def _is_power_or_spotfree_or_accessory(p: MacProduct) -> bool:
        n = p.product_name.lower()
        c = (p.category or "").lower()
        return ("charg" in n) or ("power" in n) or ("bank" in n) or (c in {"charger", "accessory", "cleaning", "peripheral"}) or ("spray" in n) or ("spotfree" in n)

    # ------------------------- Core -------------------------- #
    def _build_rows(self, products: List[MacProduct]) -> List[List[MacProduct]]:
        spacing = 18
        max_items_per_row = 8

        # Privacy row first (Row 1)
        privacy_candidates = [p for p in products if self._is_privacy(p)]
        privacy_row_base = privacy_candidates[:10]  # over-select; packing trims
        # Estimate a generous width target from first few privacy items
        if privacy_row_base:
            w_samples = [self._w_h(p)[0] for p in privacy_row_base[:6]]
            privacy_target_w = sum(w_samples) + spacing * max(0, len(w_samples) - 1)
        else:
            privacy_target_w = 1000
        # Force exactly 3 privacy filters in Row 1
        row1 = self._pack_row_by_width(privacy_row_base, privacy_target_w, 3, spacing)
        row1 = row1[:3]

        # Row 2: hubs/7-in-1 and similar (exclude keyboards)
        hub_like = [p for p in products if self._is_hub_like(p) and not self._is_keyboard(p)]
        row2 = self._pack_row_by_width(hub_like, privacy_target_w, max_items_per_row, spacing)

        # Row 3: spotfree/chargers/accessory (exclude keyboards)
        power_like = [p for p in products if self._is_power_or_spotfree_or_accessory(p) and not self._is_keyboard(p)]
        row3 = self._pack_row_by_width(power_like, privacy_target_w, max_items_per_row, spacing)

        # Row 4: exactly 3 keyboard covers centered
        keyboards = [p for p in products if self._is_keyboard(p)]
        row4 = keyboards[:3]
        if len(row4) < 3 and keyboards:
            # Duplicate top keyboard to reach 3
            while len(row4) < 3:
                row4.append(keyboards[0])

        # Remove any keyboard from rows 1–3 if they slipped in
        def strip_keyboards(row: List[MacProduct]) -> List[MacProduct]:
            return [p for p in row if not self._is_keyboard(p)]
        row1, row2, row3 = map(strip_keyboards, (row1, row2, row3))

        # Ensure Rows 1–3 are not empty; fallback to any high-priority products (non-keyboards)
        def fallback(candidates: List[MacProduct]) -> List[MacProduct]:
            pool = [p for p in candidates if not self._is_keyboard(p)]
            return pool[:max_items_per_row]
        if not row1:
            row1 = fallback(products)
        if not row2:
            row2 = fallback(products)
        if not row3:
            row3 = fallback(products)

        return [row1, row2, row3, row4]

    # ------------------------ Rendering ---------------------- #
    def _render(self, grid: List[List[MacProduct]], store_name: str, wall_number: int) -> str:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        spacing = 18
        row_gap = 42
        top_margin = 130
        bottom_margin = 70

        # Precompute widths/heights
        row_dims: List[List[Tuple[float, float]]] = [[self._w_h(p) for p in row] for row in grid]
        row_heights = [max((h for w, h in dims), default=0) for dims in row_dims]
        row_widths = [sum((w for w, h in dims)) + spacing * max(0, len(dims) - 1) for dims in row_dims]

        canvas_w = int(max(1400, max(row_widths) + 220))
        canvas_h = int(max(800, sum(row_heights) + row_gap * (len(grid) - 1) + top_margin + bottom_margin))

        fig, ax = plt.subplots(figsize=(canvas_w/100, canvas_h/100))
        ax.set_facecolor("#FFFFFF")
        ax.set_xlim(0, canvas_w)
        ax.set_ylim(0, canvas_h)
        ax.axis("off")

        # Title
        ax.text(canvas_w/2, canvas_h - 50,
                f"{store_name.upper()} - MAC ACCESSORIES WALL {wall_number}",
                fontsize=20, fontweight="bold", ha="center", va="center", color="#2C3E50")
        ax.text(canvas_w/2, canvas_h - 85,
                f"Professional Shelf Layout | {sum(len(r) for r in grid)} Products | Dimension-Optimized",
                fontsize=12, ha="center", va="center", color="#7F8C8D")

        # Helpers for color contrast and text fitting
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        def is_dark(hex_color: str) -> bool:
            r, g, b = hex_to_rgb(hex_color)
            # Relative luminance
            lum = 0.2126*r + 0.7152*g + 0.0722*b
            return lum < 150
        def truncate(text: str, max_px: float, px_per_char: float = 6.5) -> str:
            max_chars = max(6, int(max_px / px_per_char))
            return text if len(text) <= max_chars else text[:max_chars-1] + '…'

        y = canvas_h - top_margin
        for r_idx, row in enumerate(grid):
            dims = row_dims[r_idx]
            if not dims:
                continue
            row_h = row_heights[r_idx]
            row_w = row_widths[r_idx]
            row_center_y = y - row_h/2
            start_x = (canvas_w - row_w) / 2
            x = start_x
            for p, (w, h) in zip(row, dims):
                # Brand color coding
                brand = (p.brand or '').lower()
                brand_colors = {
                    'apple': '#007AFF', 'belkin': '#FF6B35', 'logitech': '#00B04F', 'anker': '#FF3B30',
                    'satechi': '#5856D6', 'hyper': '#FF9500', 'caldigit': '#34C759', 'owc': '#AF52DE',
                    'ugreen': '#32D74B', 'tekne': '#FF2D92', 'pulse': '#007AFF', 'gripp': '#1D1D1F'
                }
                fill = brand_colors.get(brand, '#E9F2FF')
                edge = '#AEB6BF' if brand not in ('gripp',) else '#333333'
                rect = Rectangle((x, row_center_y - h/2), w, h, facecolor=fill, edgecolor=edge)
                ax.add_patch(rect)

                # Determine text colors and sizes (no stretching)
                dark_bg = is_dark(fill)
                name_color = '#FFFFFF' if dark_bg else '#1D1D1F'
                sub_color = '#F2F2F7' if dark_bg else '#7F8C8D'
                name_fs = max(7, min(12, w/18))
                sub_fs = max(6, min(10, w/22))

                # Primary line: for privacy, show product name; else brand
                cat = (p.category or '').lower()
                if 'privacy' in cat:
                    primary_text = p.product_name
                    secondary_text = p.brand.upper() if p.brand else ''
                else:
                    primary_text = p.brand.upper() if p.brand else p.product_name
                    secondary_text = p.product_name

                ax.text(
                    x + w/2,
                    row_center_y + min(10, h*0.28),
                    truncate(primary_text, w*0.9),
                    fontsize=name_fs,
                    ha='center', va='center', color=name_color, clip_on=True
                )
                ax.text(
                    x + w/2,
                    row_center_y - h/2 + 10,
                    truncate(secondary_text, w*0.92),
                    fontsize=sub_fs,
                    ha='center', va='bottom', color=sub_color, clip_on=True
                )
                x += w + spacing
            y -= row_h + row_gap

        # Use consistent naming with other generators
        store_slug = store_name.lower().replace(' ', '_').replace('-', '_')
        fname = f"mac_wall_{wall_number}_{store_slug}.png"
        out_path = str(OUTPUT_DIR / fname)
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return out_path

    # --------------------- Public API ------------------------ #
    def generate_store_planograms(self, store_name: str, num_walls: int) -> Dict[str, str]:
        products = self.load_mac_data()
        # Filter to approved TPA brands if needed (soft filter)
        approved = {"gripp", "pulse", "tekne", "belkin", "alogic", "anker", "satechi"}
        products = [p for p in products if (p.brand or "").lower() in approved]

        # Generate the requested number of walls (typically 1 for Mac accessories)
        results = {}
        for wall_num in range(1, min(num_walls + 1, 2)):  # Max 1 wall for now
            grid = self._build_rows(products)
            out = self._render(grid, store_name, wall_num)
            results[f"wall_{wall_num}"] = out
        return results

