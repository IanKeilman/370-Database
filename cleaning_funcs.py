import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from scipy.ndimage import binary_dilation
from scipy.spatial import KDTree

# Configuration constants
OCR_REGIONS = {
    "min_top_left": {"x": 36,  "y": 31,  "width": 34, "height": 15},
    "min_right":    {"x": 199, "y": 261, "width": 36, "height": 19},
    "max_top_left": {"x": 35,  "y": 45,  "width": 35, "height": 17},
    "max_right":    {"x": 197, "y": 38,  "width": 38, "height": 18},
}

WHITE_TOLERANCE = 150      # how "white" a pixel must be (0–255 scale)
NEIGHBOR_COUNT = 150       # how many non‑white neighbors to average

WHITE_BOXES = [
    {"x": -1,  "y": 0,   "width": 71, "height": 62},
    {"x": 166, "y": 3,   "width": 70, "height": 26},
    {"x": 197, "y": 36,  "width": 38, "height": 244},
    {"x": 177, "y": 299, "width": 54, "height": 21},
    {"x": 0,   "y": 302, "width": 46, "height": 17},
]

GREEN_BOX = {"x": 99, "y": 140, "width": 38, "height": 41}
SMOOTH_TEMPERATURE_BAR = True
TEMPERATURE_BAR_BOX = {"x": 215, "y": 56, "width": 20, "height": 209}


def run_ocr_on_coords(image_path, regions=OCR_REGIONS, conf_threshold=80):
    """
    Crop each named region, enhance contrast, sharpen, then run OCR.
    Returns a dict with 'min', 'max', their confidence scores, and flags if below threshold.
    """
    img = Image.open(image_path)
    raw_results = {}

    # Run OCR on every region
    for label, box in regions.items():
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]
        crop = img.crop((x, y, x + w, y + h))

        # Pre‑process: grayscale → boost contrast → sharpen
        gray     = ImageOps.grayscale(crop)
        enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
        sharp    = enhanced.filter(ImageFilter.SHARPEN)

        # Extract text data
        data = pytesseract.image_to_data(
            sharp,
            output_type=pytesseract.Output.DICT,
            config="--psm 6 -c tessedit_char_whitelist=0123456789."
        )

        # Select highest-confidence fragment
        best_text, best_conf = "", -1
        for txt, conf in zip(data["text"], data["conf"]):
            try:
                c = float(conf)
            except ValueError:
                continue
            t = txt.strip()
            if t and c > best_conf:
                best_text, best_conf = t, c
        raw_results[label] = {"value": best_text, "conf": best_conf}

    # Choose best min and max
    def choose(a, b):
        r1, r2 = raw_results[a], raw_results[b]
        return r1 if r1["conf"] >= r2["conf"] else r2

    min_res = choose("min_top_left", "min_right")
    max_res = choose("max_top_left", "max_right")

    return {
        "min":      min_res["value"],
        "min_conf": min_res["conf"],
        "min_flag": min_res["conf"] < conf_threshold,
        "max":      max_res["value"],
        "max_conf": max_res["conf"],
        "max_flag": max_res["conf"] < conf_threshold,
    }


def smooth_pixels(
    image_path, output_path,
    tolerance=WHITE_TOLERANCE, neighbor_count=NEIGHBOR_COUNT,
    white_boxes=WHITE_BOXES, green_box=GREEN_BOX,
    smooth_bar=SMOOTH_TEMPERATURE_BAR, bar_box=TEMPERATURE_BAR_BOX
):
    """
    1) Find near‑white pixels (>= 255‑tolerance), dilate mask by 2px.
    2) Keep only those pixels inside white_boxes.
    3) Replace each by average of k nearest non‑white pixels (two passes).
    4) k‑NN blur for green pixels in green_box.
    5) Optionally blur temperature bar in bar_box.
    """
    img  = Image.open(image_path).convert("RGB")
    arr  = np.array(img)
    h, w = arr.shape[:2]
    white_t = 255 - tolerance

    # 1) White mask + dilation
    white_mask = np.all(arr >= white_t, axis=-1)
    struct     = np.ones((5, 5), bool)
    dilated    = binary_dilation(white_mask, structure=struct)

    # 2) Filter to white_boxes
    coords = np.argwhere(dilated)
    keep = []
    for y, x in coords:
        for b in white_boxes:
            if b["x"] <= x < b["x"]+b["width"] and b["y"] <= y < b["y"]+b["height"]:
                keep.append((y, x))
                break
    white_coords = np.array(keep)
    if white_coords.size == 0:
        print("No white pixels to smooth.")
        return 0

    non_white = np.argwhere(~dilated)
    tree      = KDTree(non_white)

    smoothed = arr.copy()
    changed  = 0
    # 3) Two passes k-NN blur
    for _ in range(2):
        for y, x in white_coords:
            dists, idxs = tree.query((y, x), k=neighbor_count)
            nbrs        = non_white[idxs]
            colors      = arr[nbrs[:,0], nbrs[:,1]]
            avg_color   = colors.mean(axis=0).astype(np.uint8)
            if not np.array_equal(smoothed[y, x], avg_color):
                smoothed[y, x] = avg_color
                changed      += 1
        arr = smoothed.copy()

    # 4) Blur green pixels
    gx, gy, gw, gh = green_box.values()
    green_coords = []
    green_box_mask = np.zeros_like(white_mask)
    for i in range(gy, gy+gh):
        for j in range(gx, gx+gw):
            r, g, b = arr[i, j]
            if g > 100 and g > r and g > b:
                green_coords.append((i, j))
                green_box_mask[i, j] = True
    green_coords = np.array(green_coords)
    outside_coords = np.argwhere(~green_box_mask)
    if outside_coords.size and green_coords.size:
        green_tree = KDTree(outside_coords)
        for y, x in green_coords:
            k = min(neighbor_count, len(outside_coords))
            _, idxs = green_tree.query((y, x), k=k)
            nbrs   = outside_coords[idxs]
            avg    = arr[nbrs[:,0], nbrs[:,1]].mean(axis=0).astype(np.uint8)
            smoothed[y, x] = avg
            changed += 1

    # 5) Blur temperature bar
    if smooth_bar:
        bx, by, bw, bh = bar_box.values()
        inside = [(y, x)
                  for y in range(by, min(by+bh, h))
                  for x in range(bx, min(bx+bw, w))]
        outside = np.argwhere(~(
            (np.arange(h)[:,None] >= by) & (np.arange(h)[:,None] < by+bh) &
            (np.arange(w)[None,:] >= bx) & (np.arange(w)[None,:] < bx+bw)
        ))
        bar_tree = KDTree(outside)
        for y, x in inside:
            _, idxs = bar_tree.query((y, x), k=min(neighbor_count, len(outside)))
            nbrs    = outside[idxs]
            avg     = smoothed[nbrs[:,0], nbrs[:,1]].mean(axis=0).astype(np.uint8)
            smoothed[y, x] = avg
            changed += 1
        print("Temperature bar smoothed.")

    Image.fromarray(smoothed).save(output_path)
    print(f"Saved smoothed image to {output_path}")
    return changed
