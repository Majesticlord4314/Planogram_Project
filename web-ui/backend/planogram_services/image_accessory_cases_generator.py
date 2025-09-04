#!/usr/bin/env python3
"""
Image Accessory-Based Cases & Covers Planogram Generator
- Uses actual product images (from merged folder) and sales data
- Dynamic grid rules by store size (flagship/medium/express)
- Flagship: 8x6, top 4 rows Apple, bottom 4 rows TPA; 4 walls for Base/Plus/Pro/Pro Max; mix screen protectors in TPA rows
- Medium: 8x6, merge series column-wise, 1–2 Apple rows
- Express: 5x6, 2–3 Apple rows, each column dedicated to a series
- Outputs planogram image + neat text report (includes top sellers even if image missing)
"""
from pathlib import Path
from typing import Dict, List, Tuple
import re
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
# Optional OpenCV for advanced cropping
try:
    import cv2  # type: ignore
except Exception:
    cv2 = None
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2].parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
IMAGES_DIR = PROJECT_ROOT / 'pdf_databank' / 'output' / 'images' / 'combined'
SALES_CSV = PROJECT_ROOT / 'data' / 'raw' / 'accessories' / 'cases_sales.csv'

SERIES_ORDER = ['base', 'plus', 'pro', 'pro max']
SERIES_PATTERNS = {
    'base': re.compile(r'\biphone\s*1[0-9]\b(?!\s*(pro|max|plus))', re.I),
    'plus': re.compile(r'\biphone\s*1[0-9]\s*plus\b', re.I),
    'pro': re.compile(r'\biphone\s*1[0-9]\s*pro\b(?!\s*max)', re.I),
    'pro max': re.compile(r'\biphone\s*1[0-9]\s*pro\s*max\b', re.I),
}
BRAND_PATTERNS = {
    'apple': re.compile(r'\bapple\b|\biphone\b', re.I),
    'gripp': re.compile(r'\bgripp\b', re.I),
    'tekne': re.compile(r'\btekne\b|\bpulse\b', re.I),
    'pulse': re.compile(r'\bpulse\b', re.I),
}

class ImageAccessoryCasesGenerator:
    def __init__(self):
        self.images_dir = IMAGES_DIR
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.title_font = ImageFont.truetype('Arial.ttf', 24)
            self.sub_font = ImageFont.truetype('Arial.ttf', 14)
            self.label_font = ImageFont.truetype('Arial.ttf', 10)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.sub_font = ImageFont.load_default()
            self.label_font = ImageFont.load_default()

    # ---------------------- Data Loading ----------------------
    def load_sales(self) -> pd.DataFrame:
        if not SALES_CSV.exists():
            return pd.DataFrame()
        df = pd.read_csv(SALES_CSV)
        df.columns = df.columns.str.strip().str.lower()
        df = df[df['pureqty'].notna() & (df['pureqty'] > 0)]
        df['series_bucket'] = df['series'].astype(str).str.lower().apply(self.bucket_series)
        df['brand_norm'] = df['brand'].astype(str).str.strip().str.lower()
        return df.sort_values('pureqty', ascending=False)

    def index_images(self) -> List[Dict]:
        items = []
        if not self.images_dir.exists():
            return items
        for p in sorted(self.images_dir.glob('*.jpg')):
            name = p.name.lower()
            brand = self.detect_brand(name)
            series_bucket = self.bucket_series(name)
            is_case = 'case' in name
            is_screen = ('protector' in name) or ('glass' in name)
            items.append({
                'path': p,
                'name': p.name,
                'brand': brand,
                'series_bucket': series_bucket,
                'is_case': is_case,
                'is_screen': is_screen,
            })
        return items

    def detect_brand(self, text: str) -> str:
        t = text.lower()
        if BRAND_PATTERNS['gripp'].search(t):
            return 'gripp'
        if BRAND_PATTERNS['tekne'].search(t):
            return 'tekne'
        # If filename style like "iphone ... silicone case" assume Apple
        if 'iphone' in t and 'case' in t and not ('gripp' in t or 'tekne' in t or 'pulse' in t):
            return 'apple'
        return 'tpa'

    def bucket_series(self, text: str) -> str:
        t = str(text).lower()
        if SERIES_PATTERNS['pro max'].search(t):
            return 'pro max'
        if SERIES_PATTERNS['pro'].search(t):
            return 'pro'
        if SERIES_PATTERNS['plus'].search(t):
            return 'plus'
        # Default to base if iPhone is present
        if 'iphone' in t:
            return 'base'
        return 'unknown'

    # ---------------------- Layout Rules ----------------------
    def store_category(self, total_store_walls: int) -> str:
        if total_store_walls >= 8:
            return 'flagship'
        if total_store_walls >= 2:
            return 'medium'
        return 'express'

    def grid_for_store(self, store_cat: str) -> Tuple[int, int]:
        if store_cat == 'flagship':
            return (8, 6)
        if store_cat == 'medium':
            return (8, 6)
        return (5, 6)

    def apple_rows_for_store(self, store_cat: str) -> int:
        if store_cat == 'flagship':
            return 4
        if store_cat == 'medium':
            return 2
        return 3
    def _opencv_crop(self, img: Image.Image, max_tilt: float = 20) -> Image.Image:
        if cv2 is None:
            return img
        try:
            arr = np.array(img.convert('RGB'))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            gray = cv2.medianBlur(gray, 3)
            # Edge detection
            v = np.median(gray)
            sigma = 0.33
            low = int(max(0, (1.0 - sigma) * v))
            high = int(min(255, (1.0 + sigma) * v))
            edges = cv2.Canny(gray, low, high)
            # Close gaps and emphasize rectangles
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            edges = cv2.dilate(edges, kernel, iterations=1)
            # Find contours
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not cnts:
                return img
            # Choose the largest plausible rectangular contour by area
            cnt = max(cnts, key=cv2.contourArea)
            rect = cv2.minAreaRect(cnt)  # ((cx,cy),(w,h),angle)
            (w,h) = rect[1]
            angle = rect[2]
            # Normalize angle: OpenCV returns [-90,0)
            if w < h:
                angle = angle
            else:
                angle = angle + 90
            rotated = arr
            if abs(angle) <= max_tilt:
                # Rotate around center
                (H,W) = gray.shape
                M = cv2.getRotationMatrix2D((W//2, H//2), angle, 1.0)
                rotated = cv2.warpAffine(arr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))
            # Recompute on rotated image
            gray2 = cv2.cvtColor(rotated, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.medianBlur(gray2, 3)
            edges2 = cv2.Canny(gray2, low, high)
            edges2 = cv2.dilate(edges2, kernel, iterations=1)
            cnts2, _ = cv2.findContours(edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnt2 = max(cnts2, key=cv2.contourArea)
            rect2 = cv2.minAreaRect(cnt2)
            box = cv2.boxPoints(rect2)
            box = box.astype(int)
            x,y,w2,h2 = cv2.boundingRect(box)
            crop = rotated[y:y+h2, x:x+w2]
            out = Image.fromarray(crop)
            if out.width > out.height:
                out = out.rotate(90, expand=True, fillcolor='white')
            return out
        except Exception:
            return img
        if store_cat == 'flagship':
            return 4
        if store_cat == 'medium':
            return 2  # can tune to 1–2 dynamically later
        return 3  # express 2–3 rows; choose 3 by default

    # ---------------------- Image Utils ----------------------
    def crop_to_content(self, img: Image.Image, brand: str = None, thresh_bg: int = 248, pad: int = 6) -> Image.Image:
        # 1) Light denoise
        g = img.convert('L').filter(ImageFilter.MedianFilter(size=3))
        arr = np.asarray(g)
        H, W = arr.shape

        # 2) Estimate and correct small skew using gradient PCA (±10°)
        try:
            gx = np.abs(np.diff(arr, axis=1, prepend=arr[:, :1]))
            gy = np.abs(np.diff(arr, axis=0, prepend=arr[:1, :]))
            grad = gx + gy
            coords = np.column_stack(np.where(grad > np.percentile(grad, 92)))
            if coords.shape[0] > 50:
                c = coords - coords.mean(0)
                cov = (c.T @ c) / max(1, c.shape[0])
                vals, vecs = np.linalg.eigh(cov)
                v = vecs[:, np.argmax(vals)]

                angle = np.degrees(np.arctan2(v[0], v[1]))
                if abs(angle) <= 10:
                    img = img.rotate(-angle, expand=True, fillcolor='white')
                    g = img.convert('L').filter(ImageFilter.MedianFilter(size=3))
                    arr = np.asarray(g)
                    H, W = arr.shape
                    gx = np.abs(np.diff(arr, axis=1, prepend=arr[:, :1]))
                    gy = np.abs(np.diff(arr, axis=0, prepend=arr[:1, :]))
                    grad = gx + gy
        except Exception:
            pass

        # 3) Energy-based tight crop (minimal trimming)
        k = 13
        row_energy = np.convolve(grad.sum(axis=1), np.ones(k)/k, mode='same')
        col_energy = np.convolve(grad.sum(axis=0), np.ones(k)/k, mode='same')
        # Lower thresholds to hug packaging tighter while keeping minimal trim
        f = 0.06 if brand == 'apple' else 0.045
        rthr = max(3.0, f * row_energy.max())
        cthr = max(3.0, f * col_energy.max())
        r_idx = np.where(row_energy > rthr)[0]
        c_idx = np.where(col_energy > cthr)[0]
        if r_idx.size and c_idx.size:
            y0 = max(0, int(r_idx[0] - pad))
            y1 = min(H, int(r_idx[-1] + pad + 1))
            x0 = max(0, int(c_idx[0] - pad))
            x1 = min(W, int(c_idx[-1] + pad + 1))
        else:
            # Fallback: robust brightness threshold box
            p95 = int(np.percentile(arr, 95))
            thresh = min(thresh_bg, max(200, p95))
            mask = arr < thresh
            if not mask.any():
                return img
            ys, xs = np.where(mask)
            y0, y1 = max(0, ys.min()-pad), min(H, ys.max()+pad)
            x0, x1 = max(0, xs.min()-pad), min(W, xs.max()+pad)

        # Mild hanger/top trim if a very bright strip remains
        top_slice = arr[max(0, y0):min(H, y0 + max(2, int(0.06*(y1-y0)))), x0:x1]
        if top_slice.size:
            local95 = np.percentile(top_slice, 95)
            global95 = np.percentile(arr, 95)
            if local95 > global95 - 2:
                y0 = min(y1-10, y0 + int(0.04*(y1-y0)))

        # 4) Validate and finalize crop
        if x1 - x0 < 10 or y1 - y0 < 10:
            return img
        cropped = img.crop((x0, y0, x1, y1))
        # Portrait preference
        if cropped.width > cropped.height:
            cropped = cropped.rotate(90, expand=True, fillcolor='white')
        return cropped

    def letterbox_resize(self, img: Image.Image, target_size: Tuple[int, int], bg: str='white') -> Image.Image:
        tw, th = target_size
        # Keep aspect and center into target canvas (no stretching)
        r = min(tw / img.width, th / img.height)
        nw, nh = max(1, int(img.width * r)), max(1, int(img.height * r))
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', (tw, th), bg)
        ox = (tw - nw) // 2
        oy = (th - nh) // 2
        canvas.paste(resized, (ox, oy))
        return canvas

    def crop_packaging(self, img: Image.Image, brand: str, mode: str = 'balanced') -> Image.Image:
        # mode: 'balanced' (tight but safe) or 'max_tight' (more aggressive)
        if mode == 'max_tight' and cv2 is not None:
            return self._opencv_crop(img)
        # fallback/balanced: energy-based crop
        return self.crop_to_content(img, brand=brand)

    # ---------------------- Generation ----------------------
    def generate_store_planograms(self, store_name: str, num_walls: int, total_store_walls: int) -> Dict[str, bool]:
        sales = self.load_sales()
        images = self.index_images()
        store_cat = self.store_category(total_store_walls)
        rows, cols = self.grid_for_store(store_cat)
        apple_rows = self.apple_rows_for_store(store_cat)

        results: Dict[str, bool] = {}
        # Determine series assignment per wall
        wall_series = []
        if store_cat == 'flagship' and num_walls >= 4:
            wall_series = SERIES_ORDER[:4]
        else:
            # Medium/Express: repeat merged pattern
            wall_series = ['merged'] * max(1, num_walls)

        for wall_idx in range(num_walls):
            series_key = wall_series[wall_idx] if wall_idx < len(wall_series) else 'merged'
            ok = self._generate_single_wall(store_name, wall_idx+1, series_key, store_cat, rows, cols, apple_rows, sales, images, num_walls, total_store_walls)
            results[f'wall_{wall_idx+1}'] = ok
        return results

    def _select_images(self, images: List[Dict], series_key: str, count: int, brand: str, include_screens: bool, sales: pd.DataFrame) -> List[Path]:
        # Filter images by brand and case/screen
        imgs = [it for it in images if (it['brand'] == brand or (brand=='tpa' and it['brand']!='apple'))]
        if series_key != 'merged':
            imgs = [it for it in imgs if it['series_bucket'] == series_key]
        # Add screen protectors for TPA if requested
        if include_screens and brand != 'apple':
            screen_imgs = [it for it in images if it['is_screen']]
            imgs = imgs + screen_imgs
        # Rank by sales if possible
        ranked = []
        if not sales.empty:
            for it in imgs:
                # crude join: use series bucket and brand name to estimate priority
                s = 0
                sb = it['series_bucket']
                if sb in {'base','plus','pro','pro max'}:
                    s += int(sales[sales['series_bucket']==sb]['pureqty'].sum())
                if it['brand']=='apple':
                    s += 100  # bias Apple up slightly for top rows aesthetics
                ranked.append((s, it))
            ranked.sort(key=lambda x: x[0], reverse=True)
            imgs = [it for _, it in ranked]
        # Build output list to exactly 'count' items, allowing repeats to fill facings
        out: List[Path] = []
        # First pass: unique items
        for it in imgs:
            p = it['path']
            if p not in out:
                out.append(p)
            if len(out) >= count:
                return out[:count]
        # If not enough, repeat from the start
        if imgs:
            i = 0
            while len(out) < count:
                out.append(imgs[i % len(imgs)]['path'])
                i += 1
            return out
        # Absolute fallback: if no imgs matched, try any images at all
        return [it['path'] for it in images][:count]

    def _generate_single_wall(self, store_name: str, wall_number: int, series_key: str, store_cat: str,
                              rows: int, cols: int, apple_rows: int,
                              sales: pd.DataFrame, images: List[Dict], num_walls: int, total_store_walls: int) -> bool:
        try:
            # Prepare canvas
            product_size = (140, 140) if rows==8 else (150, 150)
            spacing = 10
            margin = 40
            canvas_w = cols*(product_size[0]+spacing)+margin*2
            canvas_h = rows*(product_size[1]+spacing)+margin*2+100
            canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
            draw = ImageDraw.Draw(canvas)

            # Header
            title = f"{store_name.upper()} - CASES & COVERS WALL {wall_number}"
            sub = f"{store_cat.title()} | {rows}x{cols} grid | Apple rows: {apple_rows} | Series: {series_key}"
            tw = draw.textbbox((0,0), title, font=self.title_font)
            sx = (canvas_w - (tw[2]-tw[0]))//2
            draw.text((sx, 16), title, fill='black', font=self.title_font)
            sw = draw.textbbox((0,0), sub, font=self.sub_font)
            sx2 = (canvas_w - (sw[2]-sw[0]))//2
            draw.text((sx2, 46), sub, fill='gray', font=self.sub_font)

            # Select images
            top_count = apple_rows*cols
            bottom_count = (rows-apple_rows)*cols
            apple_imgs = self._select_images(images, series_key, top_count, 'apple', include_screens=False, sales=sales)
            tpa_imgs = self._select_images(images, series_key, bottom_count, 'tpa', include_screens=True, sales=sales)

            # Place images
            y = margin + 80
            idx_a = 0
            idx_t = 0
            for r in range(rows):
                x = margin
                for c in range(cols):
                    use_apple = r < apple_rows
                    img_path = None
                    if use_apple and idx_a < len(apple_imgs):
                        img_path = apple_imgs[idx_a]; idx_a += 1
                    elif (not use_apple) and idx_t < len(tpa_imgs):
                        img_path = tpa_imgs[idx_t]; idx_t += 1
                    if img_path:
                        try:
                            img = Image.open(img_path).convert('RGB')
                            # Use brand-aware crop and portrait normalization
                            b = 'apple' if use_apple else 'tpa'
                            # Use conservative balanced crop for reliability
                            img = self.crop_packaging(img, brand=b, mode='balanced')
                            img = self.letterbox_resize(img, product_size)
                            canvas.paste(img, (x, y))
                        except Exception:
                            pass
                    x += product_size[0] + spacing
                y += product_size[1] + spacing

            # Save outputs
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            base = f"{store_name.lower()}_wall{wall_number}_cases_images_accessory"
            out_img = OUTPUT_DIR / f"{base}.png"
            out_txt = OUTPUT_DIR / f"{base}.txt"
            canvas.save(out_img, 'PNG', dpi=(300,300))

            # Report: placed items and top sales candidates
            with open(out_txt, 'w', encoding='utf-8') as f:
                f.write(f"Cases & Covers (Accessory-based)\n")
                f.write(f"Store: {store_name}\n")
                f.write(f"Store Category: {store_cat}\n")
                f.write(f"Wall: {wall_number} of {num_walls}\n")
                f.write(f"Grid: {rows}x{cols}\n")
                f.write(f"Apple rows: {apple_rows}\n")
                f.write(f"Series: {series_key}\n\n")
                # Placed items (based on filenames)
                def fmt_name(p):
                    return Path(p).name
                f.write("Placed items (Apple rows):\n")
                for p in apple_imgs[:top_count]:
                    f.write(f"  • {fmt_name(p)}\n")
                f.write("\nPlaced items (TPA rows incl. screens):\n")
                for p in tpa_imgs[:bottom_count]:
                    f.write(f"  • {fmt_name(p)}\n")
                f.write("\n")
                if not sales.empty:
                    f.write("Top sellers by series (from cases_sales.csv):\n")
                    for s in (SERIES_ORDER if series_key=='merged' else [series_key]):
                        top_s = sales[sales['series_bucket']==s].sort_values('pureqty', ascending=False).head(15)
                        f.write(f"  {s.title()}: {len(top_s)} items\n")
                        for _, row in top_s.iterrows():
                            pname = row.get('product_name','') if 'product_name' in row else row.get('product','')
                            brand = row.get('brand','')
                            qty = int(row.get('pureqty', 0))
                            f.write(f"    • {pname} | Brand: {brand} | Sales: {qty}\n")
                        f.write("\n")
                f.write("Note: Grid uses available images only. Sales list includes best candidates even if imagery is missing.\n")

            return True
        except Exception as e:
            print('Error generating wall:', e)
            return False

if __name__ == '__main__':
    gen = ImageAccessoryCasesGenerator()
    # simple smoke test
    ok = gen.generate_store_planograms('test_store', 4, total_store_walls=10)
    print('Test:', ok)

