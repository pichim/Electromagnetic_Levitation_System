import socket
import cv2
import numpy as np

NAMES = {0: "Debug", 1: "Differenz (verstaerkt | binarisiert)", 2: "Hintergrund"}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5006))
sock.settimeout(0.5)                      # damit Strg+C und ESC sofort wirken
print("Warte auf Bilder... (ESC beendet)")

while True:
    try:
        data, _ = sock.recvfrom(65535)
    except socket.timeout:
        data = None
    if data and len(data) > 1:
        img = cv2.imdecode(np.frombuffer(data[1:], np.uint8), cv2.IMREAD_COLOR)
        if img is not None and data[0] in NAMES:
            cv2.imshow(NAMES[data[0]], img)
    if cv2.waitKey(1) == 27:
        break
cv2.destroyAllWindows()