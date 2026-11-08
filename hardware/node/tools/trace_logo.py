"""PNG logo -> clean SVG (dark shapes, holes kept) via OpenCV contours. Usage: python tools/trace_logo.py in.png out.svg"""
import sys, cv2, numpy as np
img = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
img = cv2.GaussianBlur(img, (3, 3), 0)
_, bw = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)          # dark logo -> white
bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
cnts, hier = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
h, w = bw.shape
paths = []
for c, hh in zip(cnts, hier[0]):
    if cv2.contourArea(c) < 150:
        continue
    eps = 0.0012 * cv2.arcLength(c, True)
    a = cv2.approxPolyDP(c, eps, True)[:, 0, :]
    paths.append("M" + " L".join(f"{x},{y}" for x, y in a) + " Z")
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><path fill-rule="evenodd" fill="#0f1e38" d="{" ".join(paths)}"/></svg>'
open(sys.argv[2], "w").write(svg)
print(len(paths), "contours ->", sys.argv[2])
