import time
import matplotlib.animation as anim
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.linalg import cholesky, solve_triangular


def Lin_comp_chol(y_data: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Linear compensation using Cholesky."""
    ATA = A.T @ A
    ATy = A.T @ y_data

    L = cholesky(ATA, lower=True)
    w = solve_triangular(L, ATy, lower=True)
    p = solve_triangular(L.T, w, lower=False)
    return p


_RNG = np.random.default_rng()


def fit_circle_ransac(
    x: np.ndarray,
    y: np.ndarray,
    max_iters: int = 300,
    threshold: float = 3.0,
    min_inliers: int = 25,
    min_radius: float = 5.0,
    max_radius: float = 300.0,
) -> tuple[float, float, float] | tuple[None, None, None]:
    """Robust circle fitting with RANSAC.

    Each 3-point hypothesis is solved in closed form (the circumcenter of the
    sampled triangle), and all hypotheses in a batch are scored against the
    full point set using vectorised NumPy operations. The inlier test compares
    squared distances so no per-point square root is needed.

    Returns (None, None, None) if no valid circle is found.
    """
    n_points = len(x)
    if n_points < 3:
        return None, None, None

    best_count = 0
    best_inliers: np.ndarray | None = None

    # Bound the size of the (candidates x points) distance matrix.
    chunk = max(1, min(max_iters, 1_000_000 // n_points))
    iters = 0
    while iters < max_iters:
        m = min(chunk, max_iters - iters)
        iters += m

        idx = _RNG.integers(0, n_points, size=(m, 3))
        x1, y1 = x[idx[:, 0]], y[idx[:, 0]]
        x2, y2 = x[idx[:, 1]], y[idx[:, 1]]
        x3, y3 = x[idx[:, 2]], y[idx[:, 2]]

        s1 = x1 * x1 + y1 * y1
        s2 = x2 * x2 + y2 * y2
        s3 = x3 * x3 + y3 * y3

        # Circumcenter of the sampled triangle (closed form).
        denom = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        with np.errstate(divide="ignore", invalid="ignore"):
            xc_cand = (s1 * (y2 - y3) + s2 * (y3 - y1) + s3 * (y1 - y2)) / denom
            yc_cand = (s1 * (x3 - x2) + s2 * (x1 - x3) + s3 * (x2 - x1)) / denom

        r_cand = np.hypot(x1 - xc_cand, y1 - yc_cand)

        # Plausibility check for radius size (e.g. within canvas bounds).
        valid = np.isfinite(xc_cand) & (r_cand >= min_radius) & (r_cand <= max_radius)
        if not np.any(valid):
            continue

        xc_v = xc_cand[valid][:, None]
        yc_v = yc_cand[valid][:, None]
        r_v = r_cand[valid]

        # Squared distance from every candidate center to every point.
        d2 = (x[None, :] - xc_v) ** 2 + (y[None, :] - yc_v) ** 2

        # |sqrt(d2) - r| < threshold  <=>  lo^2 < d2 < hi^2.
        lower = np.where(r_v > threshold, (r_v - threshold) ** 2, -1.0)[:, None]
        upper = (r_v + threshold)[:, None] ** 2
        inlier_mask = (d2 > lower) & (d2 < upper)
        counts = np.count_nonzero(inlier_mask, axis=1)

        k = int(np.argmax(counts))
        if counts[k] > best_count:
            best_count = int(counts[k])
            best_inliers = inlier_mask[k].copy()
            if best_count == n_points:
                break

    if best_inliers is None or best_count < min_inliers:
        return None, None, None

    # Refit with all inliers
    x_in = x[best_inliers]
    y_in = y[best_inliers]
    A_final = np.column_stack((x_in, y_in, np.ones_like(x_in)))
    b_final = x_in**2 + y_in**2

    p_final = Lin_comp_chol(b_final, A_final)
    xc = p_final[0] / 2.0
    yc = p_final[1] / 2.0
    r = np.sqrt(p_final[2] + xc**2 + yc**2)

    return xc, yc, r


# 1. Canvas setup
width = 1280
height = 720
ygrid, xgrid = np.ogrid[:height, :width]  # Precomputed once for speed

# 2. Load dataset and sort by timestamp
df = pd.read_csv("./test2.csv")
df.sort_values(by="t", inplace=True)

# Convert to contiguous NumPy arrays (searchsorted is orders of magnitude faster than df.between)
t_arr = df["t"].to_numpy()
x_arr = df["x"].to_numpy()
y_arr = df["y"].to_numpy()

# 3. Time parameters
t_window = 1000  # Duration of each temporal slice
t_step = 500  # Increment of dataStart per frame
start_base = t_arr.max() / 2.0 - 20e3
total_frames = 150  # Number of frames to animate

pos = np.zeros((total_frames, 3))

# 4. Prepare plot canvas
fig, ax = plt.subplots(figsize=(10, 6))
canvas = np.zeros((height, width), dtype=np.uint8)
im = ax.imshow(canvas, cmap="gray", origin="upper", vmin=0, vmax=1)
title_text = ax.set_title("")


def update(frame_idx: int = 10):
    current_start = start_base + frame_idx * t_step
    current_end = current_start + t_window

    # Fast binary search window slicing
    i_start = np.searchsorted(t_arr, current_start, side="left")
    i_end = np.searchsorted(t_arr, current_end, side="right")

    x_sub = x_arr[i_start:i_end]
    y_sub = y_arr[i_start:i_end]

    # Reset frame canvas
    frame_image = np.zeros((height, width), dtype=np.uint8)

    # Draw event points
    if len(x_sub) > 0:
        x_int = np.round(x_sub).astype(int)
        y_int = np.round(y_sub).astype(int)
        valid = (x_int >= 0) & (x_int < width) & (y_int >= 0) & (y_int < height)
        frame_image[y_int[valid], x_int[valid]] = 1

    start = time.process_time()
    # Fit circle and rasterize if successful
    xc, yc, r = fit_circle_ransac(x_sub, y_sub, max_iters=150, threshold=3.0)
    print((time.process_time() - start) * 1e3)

    if xc is not None:
        dist = np.sqrt((xgrid - xc) ** 2 + (ygrid - yc) ** 2)
        circle_mask = np.abs(dist - r) <= 1.0
        frame_image[circle_mask] = 1
        title_text.set_text(
            f"Frame {frame_idx:02d} | t={current_start:.0f} | "
            f"Center=({xc:.1f}, {yc:.1f}), r={r:.1f}"
        )
    else:
        title_text.set_text(
            f"Frame {frame_idx:02d} | t={current_start:.0f} | Fit Failed / Noisy"
        )

    im.set_data(frame_image)
    return im, title_text


# 5. Launch animation (interval in milliseconds between frames)
ani = anim.FuncAnimation(
    fig, update, frames=total_frames, interval=50, blit=False, repeat=True
)

plt.show()

ani.save("CircleFit.mp4", writer="ffmpeg", fps=30, dpi=120)
