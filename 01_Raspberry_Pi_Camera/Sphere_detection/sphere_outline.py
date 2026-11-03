import cv2
import numpy as np


class SphereOutline:
    """Findet den Umriss der Kugel und merkt sich die letzte Position (ROI).

    mode="edges":     Canny-Kanten, geeignet wenn nur ein Teil der Kugel
                      sichtbar ist (liefert Kreisbogen-Punkte).
    mode="threshold": Schwellwert auf der Fläche, optional mit Hochpass.
    """

    def __init__(self, mode="edges", thresh=128, invert=False, use_otsu=False,
                 blur=3, hp_kernel=0, canny_lo=30, canny_hi=90, min_len=15,
                 min_area=20, max_area=None, roi_scale=2.5, roi_pad=20,
                 r_min=10, r_max=80, fit_tol=2.0, sharpen=0.0, min_span=4,diff_thresh=50):
        self.mode = mode
        self.thresh = thresh
        self.invert = invert
        self.use_otsu = use_otsu
        self.blur = blur
        self.hp_kernel = hp_kernel
        self.canny_lo = canny_lo
        self.canny_hi = canny_hi
        self.min_len = min_len
        self.min_area = min_area
        self.max_area = max_area
        self.roi_scale = roi_scale
        self.roi_pad = roi_pad
        self.r_min = r_min            # plausibler Kugelradius in Pixeln (Bildkoordinaten!)
        self.r_max = r_max
        self.fit_tol = fit_tol        # max. Abstand zum Kreis für "passt" (Pixel)
        self.sharpen = sharpen        # 0 = aus, z.B. 1.0 = Kanten vor Canny schärfen
        self.min_span = min_span      # Anzahl von 12 Winkelsektoren, die belegt sein müssen
        self.diff_thresh = diff_thresh   # min. Grauwert-Unterschied zum Hintergrund
        self.bg = None
        self.reset()

    def reset(self):
        self.center = None
        self.radius = None
        self.roi = None
        self.mask = None

    def _make_roi(self, w, h):
        cx, cy = self.center
        half = int(self.radius * self.roi_scale + self.roi_pad)
        x0, y0 = max(0, int(cx) - half), max(0, int(cy) - half)
        x1, y1 = min(w, int(cx) + half), min(h, int(cy) + half)
        return x0, y0, x1, y1

    def _highpass(self, sub):
        """Lokalen Hintergrund abziehen, Mittelwert auf 128 legen."""
        bg = cv2.blur(sub, (self.hp_kernel, self.hp_kernel))
        return cv2.addWeighted(sub, 1.0, bg, -1.0, 128)

    @staticmethod
    def _circle_lsq(p):
        """Schneller algebraischer Kreisfit. Gibt xc, yc, r zurück oder None."""
        A = np.column_stack((p[:, 0], p[:, 1], np.ones(len(p))))
        b = p[:, 0] ** 2 + p[:, 1] ** 2
        sol = np.linalg.lstsq(A, b, rcond=None)[0]
        xc, yc = sol[0] / 2.0, sol[1] / 2.0
        r2 = sol[2] + xc * xc + yc * yc
        if r2 <= 0:
            return None
        return xc, yc, float(np.sqrt(r2))

    def _search_edges(self, sub, x0, y0):
        if self.blur:
            sub = cv2.GaussianBlur(sub, (self.blur, self.blur), 0)
        if self.sharpen:
            soft = cv2.GaussianBlur(sub, (0, 0), 2.0)
            sub = cv2.addWeighted(sub, 1.0 + self.sharpen, soft, -self.sharpen, 0)

        if self.bg is not None:
            # sub ist bereits binär: Rauschen entfernen, Aussenkontur nehmen
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            sub = cv2.morphologyEx(sub, cv2.MORPH_OPEN, k)    # Streupunkte weg
            edges = cv2.morphologyEx(sub, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        else:
            edges = cv2.Canny(sub, self.canny_lo, self.canny_hi, L2gradient=True)

        #edges = cv2.Canny(sub, self.canny_lo, self.canny_hi, L2gradient=True)
        joined = cv2.dilate(edges, np.ones((3, 3), np.uint8))   # Lücken schliessen
        n, labels, stats, _ = cv2.connectedComponentsWithStats(joined, connectivity=8)

        clean = np.zeros_like(edges)          # Ergebnis: nur die Kugelkante
        self.mask = clean
        best = None                            # (score, p_local, (xc, yc, r))
        d_max = 2 * self.r_max + 4

        for i in range(1, n):
            bx, by, bw, bh, area = stats[i]
            if max(bw, bh) > d_max or max(bw, bh) < self.r_min:
                continue                       # zu gross (Halter) oder zu klein
            lab = labels[by:by + bh, bx:bx + bw] == i
            e = edges[by:by + bh, bx:bx + bw] > 0
            yy, xx = np.nonzero(lab & e)
            if len(xx) < self.min_len:
                continue
            p = np.column_stack((xx + bx, yy + by)).astype(float)   # lokale Koord.

            fit = self._circle_lsq(p)
            if fit is None:
                continue
            xc, yc, r = fit
            if not (self.r_min <= r <= self.r_max):
                continue
            d = np.abs(np.hypot(p[:, 0] - xc, p[:, 1] - yc) - r)
            ok = d < self.fit_tol
            if np.count_nonzero(ok) < 0.8 * len(p):
                continue
            p = p[ok]
            fit = self._circle_lsq(p)          # Refit nur mit Inliern
            if fit is None:
                continue
            xc, yc, r = fit

            ang = np.arctan2(p[:, 1] - yc, p[:, 0] - xc)
            sectors = np.unique(((ang + np.pi) / (2 * np.pi) * 12).astype(int) % 12)
            if len(sectors) < self.min_span:
                continue                       # Bogen zu kurz für einen stabilen Fit

            score = float(len(p))
            if self.center is not None:        # Nähe zur letzten Position belohnen
                score -= 0.5 * np.hypot(xc + x0 - self.center[0],
                                        yc + y0 - self.center[1])
            if best is None or score > best[0]:
                best = (score, p, (xc, yc, r))

        if best is None:
            return None
        _, p, (xc, yc, r) = best
        clean[p[:, 1].astype(int), p[:, 0].astype(int)] = 255
        pts = (p + (x0, y0)).astype(int)
        bbox = cv2.boundingRect(pts.reshape(-1, 1, 2))
        return pts, (xc + x0, yc + y0), r, bbox

    def _search_threshold(self, sub, x0, y0):
        if self.hp_kernel:
            sub = self._highpass(sub)
        if self.blur:
            sub = cv2.GaussianBlur(sub, (self.blur, self.blur), 0)
        flag = cv2.THRESH_BINARY_INV if self.invert else cv2.THRESH_BINARY
        if self.use_otsu:
            _, mask = cv2.threshold(sub, 0, 255, flag | cv2.THRESH_OTSU)
        else:
            _, mask = cv2.threshold(sub, self.thresh, 255, flag)
        self.mask = mask
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_NONE, offset=(x0, y0))
        if not cnts:
            return None
        c = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(c)
        if area < self.min_area or (self.max_area and area > self.max_area):
            return None
        m = cv2.moments(c)
        center = (m["m10"] / m["m00"], m["m01"] / m["m00"])
        radius = float(np.sqrt(area / np.pi))
        return c.reshape(-1, 2), center, radius, cv2.boundingRect(c)

    def _search(self, gray, roi):
        x0, y0, x1, y1 = roi
        sub = gray[y0:y1, x0:x1]
        if self.bg is not None:
            sub = self._subtract_bg(sub, x0, y0)      # neu
        self.roi = roi
        if self.mode == "edges":
            return self._search_edges(sub, x0, y0)
        return self._search_threshold(sub, x0, y0)

    @staticmethod
    def _clipped(bbox, roi, w, h):
        """True, wenn der Umriss den ROI-Rand berührt (ausser am Bildrand)."""
        x0, y0, x1, y1 = roi
        bx, by, bw, bh = bbox
        return ((bx <= x0 and x0 > 0) or (by <= y0 and y0 > 0) or
                (bx + bw >= x1 and x1 < w) or (by + bh >= y1 and y1 < h))

    def detect(self, gray):
        """Gibt die Umrisspunkte als (N, 2)-Array (x, y) zurück oder None."""
        h, w = gray.shape[:2]
        res = None

        if self.center is not None:                    # 1. Suche im ROI
            roi = self._make_roi(w, h)
            res = self._search(gray, roi)
            if res is not None and self._clipped(res[3], roi, w, h):
                res = None

        if res is None:                                # 2. ganzes Bild
            res = self._search(gray, (0, 0, w, h))

        if res is None:
            self.center = self.radius = None
            return None

        pts, self.center, self.radius, _ = res
        return pts
    def set_background(self, bg):
        """Hintergrundbild (uint8, Graustufen) setzen oder None zum Abschalten."""
        self.bg = None if bg is None else bg.copy()
        self.reset()

    def _subtract_bg(self, sub, x0, y0):
        """Differenz zum Hintergrund, binarisiert und entrauscht."""
        h, w = sub.shape[:2]
        diff = cv2.absdiff(sub, self.bg[y0:y0 + h, x0:x0 + w])
        _, binimg = cv2.threshold(diff, self.diff_thresh, 255, cv2.THRESH_BINARY)
        return cv2.medianBlur(binimg, 3)