with open(r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js", "r", encoding="utf-8") as f:
    lines = [line.rstrip("\r\n") for line in f]

def print_range(name, start, end):
    print(f"=== {name} ({start} to {end}) ===")
    for k in range(start, end + 1):
        print(f"{k}: {lines[k]}")
    print()

print_range("1. Sports event buttons", 4511, 4533)
print_range("2. deleteSportsEvent", 4631, 4642)
print_range("3. deleteCurrentEventResults", 5204, 5239)
print_range("4. deleteCrossCountryCategoryResults overview", 5533, 5537)
print_range("5. deleteCrossCountryCategoryResults func", 5660, 5684)
