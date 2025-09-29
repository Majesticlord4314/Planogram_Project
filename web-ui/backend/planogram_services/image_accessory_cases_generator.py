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
            
        # Enhanced case detection patterns (handle underscores and spaces)
        CASE_PATTERNS = [
            re.compile(r'iphone[_\s]*.*[_\s]*case', re.I),
            re.compile(r'case[_\s]*.*[_\s]*iphone', re.I), 
            re.compile(r'silicone[_\s]*.*[_\s]*case', re.I),
            re.compile(r'clear[_\s]*.*[_\s]*case', re.I),
            re.compile(r'magsafe[_\s]*.*[_\s]*case', re.I),
            re.compile(r'armou?r[_\s]*.*[_\s]*case', re.I),
            re.compile(r'crystal[_\s]*.*[_\s]*case', re.I),
            re.compile(r'protective[_\s]*.*[_\s]*case', re.I),
            re.compile(r'tough[_\s]*.*[_\s]*case', re.I),
            re.compile(r'rugged[_\s]*.*[_\s]*case', re.I),
            re.compile(r'shock[_\s]*.*[_\s]*case', re.I),
            re.compile(r'cover[_\s]*.*[_\s]*iphone', re.I),
            re.compile(r'iphone[_\s]*.*[_\s]*cover', re.I),
            re.compile(r'leather[_\s]*.*[_\s]*case', re.I),
        ]
        
        # Enhanced screen protector detection patterns (handle underscores and spaces)
        SCREEN_PATTERNS = [
            re.compile(r'screen[_\s]*.*[_\s]*protector', re.I),
            re.compile(r'tempered[_\s]*.*[_\s]*glass', re.I),
            re.compile(r'privacy[_\s]*.*[_\s]*glass', re.I),
            re.compile(r'lens[_\s]*.*[_\s]*protector', re.I),
            re.compile(r'glass[_\s]*.*[_\s]*protector', re.I),
            re.compile(r'protector[_\s]*.*[_\s]*screen', re.I),
            re.compile(r'anti[_\s]*.*[_\s]*glare', re.I),
            re.compile(r'blue[_\s]*.*[_\s]*light[_\s]*.*[_\s]*filter', re.I),
        ]
        
        # Exclusion patterns for non-cases products (handle underscores and spaces)
        EXCLUSION_PATTERNS = [
            re.compile(r'speaker', re.I),
            re.compile(r'headphone', re.I),
            re.compile(r'earphone', re.I),
            re.compile(r'earbuds', re.I),
            re.compile(r'airpods', re.I),
            re.compile(r'cable', re.I),
            re.compile(r'adapter', re.I),
            re.compile(r'hub', re.I),
            re.compile(r'watch[_\s]*.*[_\s]*strap', re.I),
            re.compile(r'strap', re.I),
            re.compile(r'band', re.I),
            re.compile(r'bag', re.I),
            re.compile(r'sleeve', re.I),
            re.compile(r'airtag', re.I),
            re.compile(r'charger', re.I),
            re.compile(r'powerbank', re.I),
            re.compile(r'power[_\s]*.*[_\s]*bank', re.I),
            re.compile(r'mouse', re.I),
            re.compile(r'keyboard', re.I),
            re.compile(r'stand', re.I),
            re.compile(r'mount', re.I),
            re.compile(r'holder', re.I),
            re.compile(r'wallet', re.I),
            re.compile(r'pouch', re.I),
        ]
        
        for p in sorted(self.images_dir.glob('*.jpg')):
            name = p.name.lower()
            
            # Check exclusion patterns first
            is_excluded = any(pattern.search(name) for pattern in EXCLUSION_PATTERNS)
            if is_excluded:
                continue  # Skip excluded products entirely
            
            brand = self.detect_brand(name)
            series_bucket = self.bucket_series(name)
            
            # Enhanced case detection with confidence scoring
            case_matches = sum(1 for pattern in CASE_PATTERNS if pattern.search(name))
            is_case = case_matches > 0
            case_confidence = min(1.0, case_matches / 3.0)  # Normalize to 0-1 scale
            
            # Enhanced screen protector detection with confidence scoring
            screen_matches = sum(1 for pattern in SCREEN_PATTERNS if pattern.search(name))
            is_screen = screen_matches > 0
            screen_confidence = min(1.0, screen_matches / 2.0)  # Normalize to 0-1 scale
            
            # Overall confidence score (higher of case or screen confidence)
            confidence_score = max(case_confidence, screen_confidence)
            
            # Validation flag for cases wall - must be case or screen with reasonable confidence
            is_valid_for_cases_wall = (is_case or is_screen) and confidence_score >= 0.3
            
            # Determine product category
            if is_case and case_confidence >= screen_confidence:
                product_category = 'iphone_case'
            elif is_screen:
                product_category = 'screen_protector'
            else:
                product_category = 'other'
            
            items.append({
                'path': p,
                'name': p.name,
                'brand': brand,
                'series_bucket': series_bucket,
                'is_case': is_case,
                'is_screen': is_screen,
                'is_valid_for_cases_wall': is_valid_for_cases_wall,
                'product_category': product_category,
                'confidence_score': confidence_score,
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

    def series_for_columns(self, cols: int) -> List[str]:
        """Assign a series bucket to each column in order, cycling through SERIES_ORDER."""
        order = SERIES_ORDER
        return [order[i % len(order)] for i in range(cols)]

    def recommend_products_for(self, sales: pd.DataFrame, series_bucket: str, brand_group: str, top_n: int) -> List[Dict]:
        """Return top-N recommended products for a given series and brand group using sales data.
        brand_group: 'apple' or 'tpa' (non-apple)
        Returns list of dicts with name, brand, qty.
        """
        if sales is None or sales.empty:
            return []
        df = sales.copy()
        df = df[df['series_bucket'] == series_bucket]
        if brand_group == 'apple':
            df = df[df['brand_norm'].str.contains('apple', na=False)]
        else:
            df = df[~df['brand_norm'].str.contains('apple', na=False)]
        df = df.sort_values('pureqty', ascending=False).head(max(0, top_n))
        out: List[Dict] = []
        for _, row in df.iterrows():
            pname = row.get('product_name', '') or row.get('product', '') or ''
            out.append({
                'name': str(pname),
                'brand': str(row.get('brand', row.get('brand_norm', ''))),
                'qty': int(row.get('pureqty', 0))
            })
        return out

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
        """
        Enhanced image selection with intelligent repetition and robust fallback mechanisms.
        
        Features:
        - Strictly filters only valid cases and screen protectors
        - Intelligent repetition that prioritizes diversity (colors, brands, series)
        - Fallback mechanisms for insufficient image inventory scenarios
        - Cross-series fallback while maintaining Apple/TPA brand separation
        - Placeholder generation capability for empty slots
        
        Requirements: 1.3, 4.1, 4.2, 4.3
        """
        # Configuration for fallback behavior
        FALLBACK_CONFIG = {
            'max_repeats_per_image': 3,
            'prioritize_diversity': True,
            'allow_cross_series_fallback': True,
            'allow_cross_brand_fallback': False,  # Keep Apple/TPA separation
            'use_placeholders_when_empty': True
        }
        
        # Step 1: Strict filtering - only validated cases and screen protectors
        allowed = [it for it in images if it.get('is_valid_for_cases_wall', False)]
        
        # Step 2: Brand-based filtering with enhanced logic
        if brand == 'apple':
            # Apple rows: Apple brand cases only (no screens, no TPA)
            candidate_imgs = [it for it in allowed if (it['brand'] == 'apple' and it['is_case'])]
        else:
            # TPA rows: Non-Apple cases and optionally screen protectors
            candidate_imgs = [it for it in allowed if (
                it['brand'] != 'apple' and 
                (it['is_case'] or (include_screens and it['is_screen']))
            )]
        
        # Step 3: Series filtering with cross-series fallback capability
        primary_imgs = candidate_imgs
        if series_key != 'merged':
            primary_imgs = [it for it in candidate_imgs if it['series_bucket'] == series_key]
            
            # Cross-series fallback if insufficient primary images
            if len(primary_imgs) < count and FALLBACK_CONFIG['allow_cross_series_fallback']:
                # Add images from other series, maintaining brand constraints
                fallback_imgs = [it for it in candidate_imgs if it['series_bucket'] != series_key]
                primary_imgs.extend(fallback_imgs)
        
        # Step 4: Enhanced ranking with diversity prioritization
        if primary_imgs:
            ranked_imgs = self._rank_images_with_diversity(primary_imgs, sales, brand)
        else:
            ranked_imgs = []
        
        # Step 5: Intelligent repetition with diversity maximization
        selected_paths = self._intelligent_image_repetition(
            ranked_imgs, count, FALLBACK_CONFIG
        )
        
        # Step 6: Final fallback mechanisms
        if len(selected_paths) < count:
            selected_paths = self._apply_fallback_mechanisms(
                selected_paths, allowed, count, brand, include_screens, FALLBACK_CONFIG
            )
        
        return selected_paths[:count]
    
    def _rank_images_with_diversity(self, images: List[Dict], sales: pd.DataFrame, brand: str) -> List[Dict]:
        """
        Rank images prioritizing both sales performance and diversity factors.
        """
        if not images:
            return []
        
        # Calculate diversity scores
        for img in images:
            diversity_score = 0
            
            # Color diversity bonus
            color = self._extract_color_from_filename(img['name'])
            if color in ['Clear', 'Black', 'White']:  # Popular base colors
                diversity_score += 10
            elif color in ['Blue', 'Green', 'Red', 'Pink']:  # Accent colors
                diversity_score += 15
            else:  # Unique colors
                diversity_score += 20
            
            # Brand diversity bonus (for TPA)
            if brand != 'apple':
                brand_bonus = {
                    'gripp': 15,
                    'pulse': 12,
                    'tekne': 10,
                    'hyphen': 8,
                }.get(img['brand'], 5)
                diversity_score += brand_bonus
            
            # Series diversity bonus
            series_bonus = {
                'pro max': 20,
                'pro': 18,
                'plus': 15,
                'base': 12,
            }.get(img['series_bucket'], 5)
            diversity_score += series_bonus
            
            img['diversity_score'] = diversity_score
        
        # Combine sales, confidence, and diversity scores
        if not sales.empty:
            ranked = []
            for img in images:
                # Sales score
                sales_score = 0
                sb = img['series_bucket']
                if sb in {'base', 'plus', 'pro', 'pro max'}:
                    sales_score = int(sales[sales['series_bucket'] == sb]['pureqty'].sum())
                
                # Apple brand bonus for aesthetics
                if img['brand'] == 'apple':
                    sales_score += 100
                
                # Confidence score (0-50 points)
                confidence_score = int(img.get('confidence_score', 0) * 50)
                
                # Diversity score
                diversity_score = img.get('diversity_score', 0)
                
                # Combined score with weights
                total_score = (
                    sales_score * 0.4 +           # 40% sales weight
                    confidence_score * 0.3 +      # 30% confidence weight  
                    diversity_score * 0.3         # 30% diversity weight
                )
                
                ranked.append((total_score, img))
            
            ranked.sort(key=lambda x: x[0], reverse=True)
            return [img for _, img in ranked]
        else:
            # No sales data: prioritize confidence and diversity
            images.sort(key=lambda x: (
                x.get('confidence_score', 0) * 0.6 + 
                x.get('diversity_score', 0) * 0.4
            ), reverse=True)
            return images
    
    def _intelligent_image_repetition(self, images: List[Dict], count: int, config: Dict) -> List[Path]:
        """
        Implement intelligent image repetition that maximizes diversity.
        """
        if not images:
            return []
        
        selected_paths = []
        usage_count = {}
        max_repeats = config['max_repeats_per_image']
        
        # Phase 1: Select unique images first
        for img in images:
            path = img['path']
            if len(selected_paths) >= count:
                break
            selected_paths.append(path)
            usage_count[path] = 1
        
        # Phase 2: Intelligent repetition if more slots needed
        if len(selected_paths) < count and config['prioritize_diversity']:
            remaining_slots = count - len(selected_paths)
            
            # Create diversity groups
            color_groups = {}
            brand_groups = {}
            series_groups = {}
            
            for img in images:
                color = self._extract_color_from_filename(img['name'])
                brand = img['brand']
                series = img['series_bucket']
                
                if color not in color_groups:
                    color_groups[color] = []
                if brand not in brand_groups:
                    brand_groups[brand] = []
                if series not in series_groups:
                    series_groups[series] = []
                
                color_groups[color].append(img)
                brand_groups[brand].append(img)
                series_groups[series].append(img)
            
            # Fill remaining slots with diversity priority
            for _ in range(remaining_slots):
                best_candidate = None
                best_diversity_score = -1
                
                for img in images:
                    path = img['path']
                    current_usage = usage_count.get(path, 0)
                    
                    # Skip if already at max repeats
                    if current_usage >= max_repeats:
                        continue
                    
                    # Calculate diversity benefit of adding this image
                    color = self._extract_color_from_filename(img['name'])
                    brand = img['brand']
                    series = img['series_bucket']
                    
                    # Count current representation of this image's attributes
                    color_count = sum(1 for p in selected_paths if 
                                    self._extract_color_from_filename(self._get_image_name_from_path(p)) == color)
                    brand_count = sum(1 for other_img in images if 
                                    other_img['brand'] == brand and other_img['path'] in selected_paths)
                    series_count = sum(1 for other_img in images if 
                                     other_img['series_bucket'] == series and other_img['path'] in selected_paths)
                    
                    # Diversity score: prefer underrepresented attributes
                    diversity_benefit = (
                        (1.0 / max(1, color_count)) * 0.4 +
                        (1.0 / max(1, brand_count)) * 0.3 +
                        (1.0 / max(1, series_count)) * 0.3
                    )
                    
                    # Penalize repeated usage
                    usage_penalty = current_usage * 0.2
                    final_score = diversity_benefit - usage_penalty
                    
                    if final_score > best_diversity_score:
                        best_diversity_score = final_score
                        best_candidate = img
                
                if best_candidate:
                    path = best_candidate['path']
                    selected_paths.append(path)
                    usage_count[path] = usage_count.get(path, 0) + 1
                else:
                    # No more candidates available, break
                    break
        
        # Phase 3: Simple repetition if diversity approach didn't fill all slots
        while len(selected_paths) < count and images:
            for img in images:
                if len(selected_paths) >= count:
                    break
                path = img['path']
                if usage_count.get(path, 0) < max_repeats:
                    selected_paths.append(path)
                    usage_count[path] = usage_count.get(path, 0) + 1
        
        return selected_paths
    
    def _apply_fallback_mechanisms(self, current_paths: List[Path], all_allowed: List[Dict], 
                                 target_count: int, brand: str, include_screens: bool, config: Dict) -> List[Path]:
        """
        Apply fallback mechanisms when insufficient images are available.
        """
        if len(current_paths) >= target_count:
            return current_paths
        
        remaining_slots = target_count - len(current_paths)
        
        # Fallback 1: Relax series constraints but maintain brand separation
        if config['allow_cross_series_fallback']:
            if brand == 'apple':
                fallback_candidates = [it for it in all_allowed if (it['brand'] == 'apple' and it['is_case'])]
            else:
                fallback_candidates = [it for it in all_allowed if (
                    it['brand'] != 'apple' and 
                    (it['is_case'] or (include_screens and it['is_screen']))
                )]
            
            # Add paths not already selected
            used_paths = set(current_paths)
            for img in fallback_candidates:
                if len(current_paths) >= target_count:
                    break
                if img['path'] not in used_paths:
                    current_paths.append(img['path'])
        
        # Fallback 2: Cross-brand fallback (only if explicitly allowed)
        if len(current_paths) < target_count and config['allow_cross_brand_fallback']:
            # This is disabled by default to maintain Apple/TPA separation
            cross_brand_candidates = [it for it in all_allowed if (
                it['is_case'] or (include_screens and it['is_screen'])
            )]
            
            used_paths = set(current_paths)
            for img in cross_brand_candidates:
                if len(current_paths) >= target_count:
                    break
                if img['path'] not in used_paths:
                    current_paths.append(img['path'])
        
        # Fallback 3: Generate placeholder paths for remaining empty slots
        if len(current_paths) < target_count and config['use_placeholders_when_empty']:
            remaining = target_count - len(current_paths)
            for i in range(remaining):
                # Create placeholder path identifier
                placeholder_path = Path(f"placeholder_{brand}_{i+1}.png")
                current_paths.append(placeholder_path)
        
        return current_paths
    
    def _extract_color_from_filename(self, filename: str) -> str:
        """Extract color information from filename for diversity scoring."""
        colors = [
            'Clear', 'Black', 'White', 'Blue', 'Green', 'Red', 'Pink', 'Purple',
            'Yellow', 'Orange', 'Gray', 'Silver', 'Gold', 'Rose Gold', 'Denim',
            'Fuchsia', 'Lake Green', 'Plum', 'Star Fruit', 'Stone Gray', 'Ultramarine'
        ]
        
        filename_lower = filename.lower()
        for color in colors:
            if color.lower() in filename_lower:
                return color
        return 'Unknown'
    
    def _get_image_name_from_path(self, path: Path) -> str:
        """Get image name from path for analysis."""
        return path.name if hasattr(path, 'name') else str(path)
    
    def _generate_placeholder_image(self, size: Tuple[int, int], brand: str, series: str, sales: pd.DataFrame) -> Image.Image:
        """
        Generate a placeholder image when no actual product image is available.
        Shows product information and indicates missing image.
        """
        width, height = size
        
        # Create base image with brand-appropriate colors
        if brand == 'apple':
            bg_color = '#F8F9FA'  # Light gray
            border_color = '#007AFF'  # Apple blue
            text_color = '#1D1D1F'  # Apple text
        else:
            bg_color = '#FFF5F0'  # Light orange
            border_color = '#FF6B35'  # TPA orange
            text_color = '#2C3E50'  # Dark blue-gray
        
        # Create image and drawing context
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw border
        border_width = 3
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=border_width)
        
        # Draw inner content area
        inner_margin = 10
        content_area = [inner_margin, inner_margin, width-inner_margin, height-inner_margin]
        
        # Get recommended product for this slot from sales data
        recommended_product = None
        if not sales.empty:
            brand_filter = 'apple' if brand == 'apple' else 'tpa'
            recommendations = self.recommend_products_for(sales, series, brand_filter, top_n=1)
            if recommendations:
                recommended_product = recommendations[0]
        
        # Text content
        try:
            # Use smaller fonts for placeholder
            title_font = ImageFont.truetype('Arial.ttf', 12)
            detail_font = ImageFont.truetype('Arial.ttf', 10)
            small_font = ImageFont.truetype('Arial.ttf', 8)
        except Exception:
            title_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Draw content
        y_pos = inner_margin + 5
        
        # Brand label
        brand_text = brand.upper()
        draw.text((width//2, y_pos), brand_text, fill=border_color, font=title_font, anchor='mt')
        y_pos += 20
        
        # Series label
        series_text = f"iPhone {series.title()}"
        draw.text((width//2, y_pos), series_text, fill=text_color, font=detail_font, anchor='mt')
        y_pos += 18
        
        # Missing image indicator
        draw.text((width//2, y_pos), "IMAGE", fill='#999999', font=detail_font, anchor='mt')
        y_pos += 15
        draw.text((width//2, y_pos), "MISSING", fill='#999999', font=detail_font, anchor='mt')
        y_pos += 20
        
        # Recommended product info if available
        if recommended_product:
            # Product name (truncated)
            product_name = recommended_product['name'][:20] + "..." if len(recommended_product['name']) > 20 else recommended_product['name']
            draw.text((width//2, y_pos), product_name, fill=text_color, font=small_font, anchor='mt')
            y_pos += 12
            
            # Sales info
            sales_text = f"Sales: {recommended_product['qty']}"
            draw.text((width//2, y_pos), sales_text, fill='#666666', font=small_font, anchor='mt')
        
        # Draw dashed pattern to indicate placeholder
        dash_length = 8
        gap_length = 4
        for i in range(0, width, dash_length + gap_length):
            draw.line([i, height-5, min(i+dash_length, width), height-5], fill='#CCCCCC', width=2)
        
        return img

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

            # Assign series per column (overrides merged visuals for better real-world layout)
            col_series = self.series_for_columns(cols) if series_key == 'merged' else [series_key]*cols

            # Preselect images per column and brand group
            col_imgs_apple: List[List[Path]] = []
            col_imgs_tpa: List[List[Path]] = []
            for c in range(cols):
                s_key = col_series[c]
                # enough to fill all apple rows and tpa rows in this column
                col_a = self._select_images(images, s_key, apple_rows, 'apple', include_screens=False, sales=sales)
                col_t = self._select_images(images, s_key, max(0, rows-apple_rows), 'tpa', include_screens=True, sales=sales)
                # If insufficient, repeat within the column
                if len(col_a) < max(1, apple_rows):
                    col_a = (col_a or []) * (apple_rows or 1)
                if len(col_t) < max(1, rows-apple_rows):
                    col_t = (col_t or []) * (rows-apple_rows or 1)
                col_imgs_apple.append(col_a[:apple_rows])
                col_imgs_tpa.append(col_t[:max(0, rows-apple_rows)])

            # Place images per cell using column selections
            y = margin + 80
            for r in range(rows):
                x = margin
                for c in range(cols):
                    use_apple = r < apple_rows
                    img_path = None
                    if use_apple and r < len(col_imgs_apple[c]):
                        img_path = col_imgs_apple[c][r]
                    elif (not use_apple):
                        rr = r - apple_rows
                        if rr < len(col_imgs_tpa[c]):
                            img_path = col_imgs_tpa[c][rr]
                    if img_path:
                        try:
                            # Check if this is a placeholder path
                            if str(img_path).startswith('placeholder_'):
                                # Generate placeholder rectangle with product info
                                img = self._generate_placeholder_image(
                                    product_size, 
                                    brand='apple' if use_apple else 'tpa',
                                    series=col_series[c],
                                    sales=sales
                                )
                                canvas.paste(img, (x, y))
                            else:
                                # Process actual image file
                                img = Image.open(img_path).convert('RGB')
                                # Use the most robust crop: OpenCV-based max_tight when available
                                b = 'apple' if use_apple else 'tpa'
                                img = self.crop_packaging(img, brand=b, mode='max_tight')
                                img = self.letterbox_resize(img, product_size)
                                canvas.paste(img, (x, y))
                        except Exception:
                            # Fallback: generate placeholder if image processing fails
                            try:
                                img = self._generate_placeholder_image(
                                    product_size,
                                    brand='apple' if use_apple else 'tpa', 
                                    series=col_series[c],
                                    sales=sales
                                )
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

            # Report: placed items and top sales candidates with per-column recommendations
            with open(out_txt, 'w', encoding='utf-8') as f:
                f.write(f"Cases & Covers (Accessory-based)\n")
                f.write(f"Store: {store_name}\n")
                f.write(f"Store Category: {store_cat}\n")
                f.write(f"Wall: {wall_number} of {num_walls}\n")
                f.write(f"Grid: {rows}x{cols}\n")
                f.write(f"Apple rows: {apple_rows}\n")
                f.write(f"Series per column: {', '.join(col_series)}\n\n")

                # Per-column placement used (images)
                for c in range(cols):
                    f.write(f"Column {c+1} | Series: {col_series[c].title()}\n")
                    f.write("  Apple rows (images used):\n")
                    for r in range(apple_rows):
                        if r < len(col_imgs_apple[c]):
                            f.write(f"    • {Path(col_imgs_apple[c][r]).name}\n")
                    f.write("  TPA rows (images used incl. screens):\n")
                    for rr in range(max(0, rows-apple_rows)):
                        if rr < len(col_imgs_tpa[c]):
                            f.write(f"    • {Path(col_imgs_tpa[c][rr]).name}\n")
                    # Recommendations from sales per column (top N for that column height)
                    rec_apple = self.recommend_products_for(sales, col_series[c], 'apple', top_n=apple_rows)
                    rec_tpa = self.recommend_products_for(sales, col_series[c], 'tpa', top_n=max(0, rows-apple_rows))
                    f.write("  Recommended (Apple):\n")
                    for rec in rec_apple:
                        f.write(f"    • {rec['name']} | Brand: {rec['brand']} | Sales: {rec['qty']}\n")
                    f.write("  Recommended (TPA incl. screens):\n")
                    for rec in rec_tpa:
                        f.write(f"    • {rec['name']} | Brand: {rec['brand']} | Sales: {rec['qty']}\n")
                    f.write("\n")

                f.write("Note: Images repeat where necessary due to limited imagery. Recommendations are based on sales and indicate the intended facings even if images are reused.\n")

            return True
        except Exception as e:
            print('Error generating wall:', e)
            return False

if __name__ == '__main__':
    gen = ImageAccessoryCasesGenerator()
    # simple smoke test
    ok = gen.generate_store_planograms('test_store', 4, total_store_walls=10)
    print('Test:', ok)

