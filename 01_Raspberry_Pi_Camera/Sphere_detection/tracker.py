import socket, struct, time
import cv2
import numpy as np
from picamera2 import Picamera2
from sphere_core import fit_circle_ransac
from sphere_outline import SphereOutline

PC_IP, PORT = "192.168.137.1", 5005
W, H = 640, 400
USE_FIT = False            # RANSAC-Kreisfit auf dem Umriss
FIT_STEP = 2              # nur jeden 2. Konturpunkt für den Fit

DEBUG = True              # für Zeitmessungen auf False
DEBUG_PORT = 5006
DEBUG_EVERY = 5
DEBUG_BG_EVERY = 20     # Hintergrundbild nur jedes 20. Debug-Bild senden (ändert sich nicht)
debug_count = 0
frame_nr = 0

TIMING = True
TIMING_PERIOD = 2.0
t_cap = t_det = t_fit = t_send = 0
n_frames = n_found = 0
t_report = time.perf_counter()

USE_BG = False          # True = Hintergrundsubtraktion, False = aus

det = SphereOutline(mode="edges", invert=False, blur=3, canny_lo=30, canny_hi=90,
                    min_len=15, roi_scale=2.5, roi_pad=20,
                    r_min=20, r_max=200, fit_tol=15.0, sharpen=0.0, min_span=4)

picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (W, H), "format": "YUV420"},
    controls={
        "FrameDurationLimits": (5000, 5000),
        "ExposureTime": 2000,
        "AnalogueGain": 4.0,
        "AeEnable": False,
    },
    buffer_count=4,
)
picam2.configure(config)
picam2.start()

#----------------------------------------------------
#Hintergrund erkennung
# Block durch "det.set_background(np.load(BG_FILE))" ersetzen, um bestehnenden Hintergrund zu laden
BG_FRAMES = 50
BG_FILE = "background.npy"          # optional zum Wiederverwenden

def capture_background():
    for _ in range(20):             # Kamera einschwingen lassen
        picam2.capture_array("main")
    acc = np.zeros((H, W), np.float32)
    for _ in range(BG_FRAMES):
        acc += picam2.capture_array("main")[:H, :]
    return (acc / BG_FRAMES).astype(np.uint8)

if USE_BG:
    input("Kugel ENTFERNEN, dann Enter drücken ... ")
    bg, bg_std = capture_background()
    np.save("background.npy", bg)
    np.save("background_std.npy", bg_std)
    det.set_background(bg, bg_std)
    input("Hintergrund gespeichert. Kugel EINSETZEN, dann Enter drücken ... ")
else:
    det.set_background(None)
#-----------------------------------------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#-----------------------------------------------------------------------------
#Additional Debug
def send_debug(ch, img, scale=0.5, quality=60):
    """Sendet ein Bild als JPEG, das erste Byte ist die Fensternummer."""
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale)
    ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if ok and len(jpg) < 60000:
        try:
            sock.sendto(bytes([ch]) + jpg.tobytes(), (PC_IP, DEBUG_PORT))
        except OSError:
            pass

#------------------------------------------------------------------------------

while True:
    t0 = time.perf_counter_ns()
    frame = picam2.capture_array("main")
    t1 = time.perf_counter_ns()

    y = frame[:H, :]
    pts = det.detect(y)                      # Umriss, nutzt letzte Position
    t2 = time.perf_counter_ns()

    xc = yc = r = None
    if pts is not None:
        xc, yc = det.center
        r = det.radius
        # if USE_FIT and len(pts) >= 10:
        #     p = pts[::FIT_STEP].astype(float)
        #     fx, fy, fr = fit_circle_ransac(
        #         p[:, 0], p[:, 1], max_iters=50, threshold=2.0,
        #         min_inliers=10, min_radius=0.6 * det.radius,
        #         max_radius=1.6 * det.radius)
        #     if fx is not None:
        #         xc, yc, r = fx, fy, fr
        #         det.center = (fx, fy)
        #         det.radius = fr                  # neu: ROI folgt dem echten Radius
    t3 = time.perf_counter_ns()

    if xc is not None:
        try:
            sock.sendto(struct.pack("<Qfff", time.monotonic_ns(), xc, yc, r),
                        (PC_IP, PORT))
        except OSError:
            pass
        n_found += 1
    t4 = time.perf_counter_ns()

    #----------------------------------------------------------------------------
    # Debug-Bild (nicht in der Zeitmessung enthalten)
    frame_nr += 1
    if DEBUG and frame_nr % DEBUG_EVERY == 0:
        debug_count += 1

        # Fenster 0: Bild mit ROI, Umriss und Fit, rechts die Maske des Detektors
        vis = cv2.cvtColor(y, cv2.COLOR_GRAY2BGR)
        full_mask = np.zeros_like(y)
        if det.roi is not None and det.mask is not None:
            x0, y0, x1, y1 = det.roi
            full_mask[y0:y1, x0:x1] = det.mask
            cv2.rectangle(vis, (x0, y0), (x1 - 1, y1 - 1), (255, 128, 0), 1)
        if pts is not None:
            vis[pts[:, 1], pts[:, 0]] = (0, 255, 255)
        if xc is not None:
            cv2.circle(vis, (int(xc), int(yc)), int(r), (0, 255, 0), 1)
            cv2.drawMarker(vis, (int(xc), int(yc)), (0, 0, 255),
                           cv2.MARKER_CROSS, 10, 1)
        send_debug(0, np.hstack((vis, cv2.cvtColor(full_mask, cv2.COLOR_GRAY2BGR))))

        if det.bg is not None:
            # Fenster 1: Differenz, links verstärkt (x4), rechts nach diff_thresh binarisiert
            diff = cv2.absdiff(y, det.bg)
            amp = cv2.convertScaleAbs(diff, alpha=4.0)
            _, binimg = cv2.threshold(diff, det.diff_thresh, 255, cv2.THRESH_BINARY)
            send_debug(1, np.hstack((amp, binimg)))

            # Fenster 2: Hintergrundbild (statisch, daher selten senden)
            if debug_count % DEBUG_BG_EVERY == 1:
                send_debug(2, det.bg)
    #---------------------------------------------------------------------------

    if TIMING:
        t_cap += t1 - t0; t_det += t2 - t1; t_fit += t3 - t2; t_send += t4 - t3
        n_frames += 1
        now = time.perf_counter()
        if now - t_report >= TIMING_PERIOD:
            dt = now - t_report
            k = n_frames * 1e6
            print(f"{n_frames/dt:6.1f} fps | warten {t_cap/k:5.2f} ms | "
                  f"detect {t_det/k:5.2f} | fit {t_fit/k:5.2f} | "
                  f"senden {t_send/k:5.2f} | "
                  f"Rechnen {(t_det+t_fit+t_send)/k:5.2f} ms | "
                  f"gefunden {n_found}/{n_frames}")
            t_cap = t_det = t_fit = t_send = 0
            n_frames = n_found = 0
            t_report = now