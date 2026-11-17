import re

def map_headers(header_row):
    field_map = {}
    for idx, cell in enumerate(header_row):
        if not cell:
            continue
        c = re.sub(r'[^a-z0-9]', '', str(cell).lower())
        
        # Guardian / parent must be checked before student name!
        if any(k in c for k in ['penjaga', 'bapa', 'ibu', 'guardian']):
            if any(k in c for k in ['tel', 'phone', 'bimbit', 'nombor', 'telefon', 'hp', 'notel']):
                field_map.setdefault('guardian_phone', idx)
            else:
                field_map.setdefault('guardian_name', idx)
        elif any(k in c for k in ['nokp', 'mykid', 'kadpengenalan', 'suratberanak', 'sijillahir', 'icnumber', 'dokumen']) or c in ('ic', 'kp'):
            field_map.setdefault('ic_number', idx)
        elif 'nama' in c or 'name' in c or 'murid' in c or 'pelajar' in c:
            if 'kelas' in c:
                field_map.setdefault('class_name', idx)
            else:
                field_map.setdefault('full_name', idx)
        elif any(k in c for k in ['tarikh', 'lahir', 'dob', 'birth']):
            field_map.setdefault('birth_date', idx)
        elif any(k in c for k in ['jantina', 'gender', 'sex']):
            field_map.setdefault('gender', idx)
        elif any(k in c for k in ['tingkatan', 'tahun', 'darjah', 'grade', 'year']):
            if 'kelas' in c:
                field_map.setdefault('class_name', idx)
            else:
                field_map.setdefault('grade', idx)
        elif any(k in c for k in ['kelas', 'class']):
            field_map.setdefault('class_name', idx)
        elif any(k in c for k in ['alamat', 'address']):
            field_map.setdefault('address', idx)
        elif any(k in c for k in ['kesihatan', 'alahan', 'health', 'penyakit']):
            field_map.setdefault('health_info', idx)
        elif any(k in c for k in ['rumah', 'rumahsukan']):
            field_map.setdefault('sport_house', idx)
        elif any(k in c for k in ['uniform', 'badanberuniform', 'unitberuniform']):
            field_map.setdefault('uniform_unit', idx)
        elif any(k in c for k in ['kelab', 'persatuan']):
            field_map.setdefault('club_society', idx)
        elif any(k in c for k in ['sukan', 'permainan']):
            field_map.setdefault('sports_game', idx)
    return field_map

# Test template headers
template_headers = [
    "Nama Penuh", "No KP / MyKid", "Tarikh Lahir (YYYY-MM-DD)", "Jantina (Lelaki/Perempuan)",
    "Tahun (1-6)", "Nama Kelas", "Nama Penjaga", "No Telefon Penjaga",
    "Alamat", "Maklumat Kesihatan", "Rumah Sukan", "Unit Beruniform",
    "Kelab Persatuan", "Sukan Permainan"
]
print("Template mapping:")
print(map_headers(template_headers))

# Test APDM style headers with Bil
apdm_headers = [
    "Bil", "Nama Murid", "No. Kad Pengenalan / MyKid", "Jantina", "Tingkatan / Kelas", "Tarikh Lahir",
    "Nama Bapa / Penjaga", "No. Tel Bimbit Penjaga", "Alamat Surat Menyurat"
]
print("\nAPDM mapping:")
print(map_headers(apdm_headers))
