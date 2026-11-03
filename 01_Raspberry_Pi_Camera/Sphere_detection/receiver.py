import socket, struct

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))
print("Warte auf Daten...")
while True:
    data, _ = sock.recvfrom(64)
    t_ns, x, y, r = struct.unpack("<Qfff", data)
    print(f"x={x:.1f}  y={y:.1f}  r={r:.1f}")