import re
import datetime

def clean_str(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "nan", "-", "tiada"):
        return None
    return s

def clean_ic(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        val = f"{int(val)}"
    s = str(val).strip().replace("-", "").replace(" ", "").replace(".", "")
    # If 11 digits and was integer missing leading 0
    if len(s) == 11 and s.isdigit():
        s = "0" + s
    return s.upper()

def clean_gender(val, ic_number=None):
    if val:
        v = str(val).strip().lower()
        if v.startswith(("l", "m")):
            return "Lelaki"
        if v.startswith(("p", "f", "w")):
            return "Perempuan"
    if ic_number and len(ic_number) == 12 and ic_number.isdigit():
        last_digit = int(ic_number[-1])
        return "Lelaki" if last_digit % 2 != 0 else "Perempuan"
    return "Lelaki"

def clean_birth_date(val, ic_number=None):
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%Y-%m-%d")
    if val:
        s = str(val).strip().split(" ")[0]
        # YYYY-MM-DD
        m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
        if m:
            y, mo, d = m.groups()
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        # DD/MM/YYYY or DD-MM-YYYY
        m2 = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
        if m2:
            d, mo, y = m2.groups()
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    
    # Fallback to IC
    if ic_number and len(ic_number) == 12 and ic_number.isdigit():
        yy = int(ic_number[:2])
        mo = int(ic_number[2:4])
        dd = int(ic_number[4:6])
        if 1 <= mo <= 12 and 1 <= dd <= 31:
            year = 2000 + yy if yy < 30 else 1900 + yy
            return f"{year:04d}-{mo:02d}-{dd:02d}"
    return None

def clean_grade(val, class_name=None):
    if val is not None:
        try:
            v_int = int(float(str(val).strip()))
            if 1 <= v_int <= 6:
                return v_int
        except Exception:
            pass
        m = re.search(r"[1-6]", str(val))
        if m:
            return int(m.group(0))
    if class_name:
        m = re.search(r"[1-6]", str(class_name))
        if m:
            return int(m.group(0))
    return 1

print("clean_ic tests:")
print("140515085123 ->", clean_ic("140515085123"))
print("140515-08-5123 ->", clean_ic("140515-08-5123"))
print("140515085123.0 ->", clean_ic(140515085123.0))
print("80101081234 ->", clean_ic(80101081234))

print("\nclean_gender tests:")
print("L ->", clean_gender("L"))
print("Perempuan ->", clean_gender("Perempuan"))
print("From IC 140515085123 ->", clean_gender(None, "140515085123"))
print("From IC 140820086244 ->", clean_gender(None, "140820086244"))

print("\nclean_birth_date tests:")
print("From IC 140515085123 ->", clean_birth_date(None, "140515085123"))
print("From string 15/05/2014 ->", clean_birth_date("15/05/2014"))
print("From string 2014-05-15 ->", clean_birth_date("2014-05-15"))

print("\nclean_grade tests:")
print("4 ->", clean_grade(4))
print("'Tahun 4' ->", clean_grade("Tahun 4"))
print("None, '5 Cemerlang' ->", clean_grade(None, "5 Cemerlang"))
