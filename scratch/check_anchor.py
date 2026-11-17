with open(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js", "r", encoding="utf-8") as f:
    lines = [line.rstrip("\r\n") for line in f]

for i in range(4522, 4534):
    print(f"L{i}: {repr(lines[i])}")
