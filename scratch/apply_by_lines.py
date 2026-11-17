import sys

file_path = r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js"

with open(file_path, "r", encoding="utf-8") as f:
    lines = [line.rstrip("\r\n") for line in f]

# 1. Sports events buttons
idx1_start = None
for i, l in enumerate(lines):
    if "${ev.status === 'Selesai' ?" in l and "deleteSportsEventResults" in lines[i+1]:
        idx1_start = i
        break
if idx1_start is not None:
    idx1_end = idx1_start + 10  # goes up to </button> of deleteSportsEvent
    new_lines_1 = [
        "            ${(ev.status === 'Selesai' && this.canDelete()) ? `",
        '            <button onclick="app.deleteSportsEventResults(${ev.id})" title="Padam Keputusan Acara" class="p-1.5 bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-lg transition">',
        '              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>',
        "            </button>",
        "            ` : ''}",
        '            <button onclick="app.openAddSportsEventModal(${ev.id})" title="Kemaskini Acara" class="p-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg transition">',
        '              <i data-lucide="edit" class="w-3.5 h-3.5"></i>',
        "            </button>",
        "            ${this.canDelete() ? `",
        '            <button onclick="app.deleteSportsEvent(${ev.id})" title="Padam Acara" class="p-1.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition">',
        '              <i data-lucide="trash-2" class="w-4 h-4"></i>',
        "            </button>",
        "            ` : ''}"
    ]
    lines[idx1_start:idx1_end + 1] = new_lines_1
    print("Replaced 1: Sports events buttons")
else:
    print("1 already replaced or not found")

# 2. deleteSportsEvent
idx2_start = None
for i, l in enumerate(lines):
    if "async deleteSportsEvent(eventId) {" in l:
        idx2_start = i
        break
assert idx2_start is not None, "idx2_start not found"
idx2_end = idx2_start
while lines[idx2_end].strip() != "},":
    idx2_end += 1

new_lines_2 = [
    "  async deleteSportsEvent(eventId) {",
    "    if (!this.canDelete()) {",
    "      Swal.fire({",
    "        icon: 'error',",
    "        title: 'Akses Ditolak',",
    "        text: 'Anda tidak mempunyai kebenaran untuk memadam acara sukan. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',",
    "        confirmButtonColor: '#1e3a8a'",
    "      });",
    "      return;",
    "    }",
    "    const result = await Swal.fire({",
    "      title: 'Padam Acara Sukan?',",
    "      text: 'Adakah anda pasti ingin memadam acara sukan ini berserta rekod keputusannya?',",
    "      icon: 'warning',",
    "      showCancelButton: true,",
    "      confirmButtonColor: '#dc2626',",
    "      cancelButtonColor: '#64748b',",
    "      confirmButtonText: 'Ya, Padam',",
    "      cancelButtonText: 'Batal'",
    "    });",
    "    if (!result.isConfirmed) return;",
    "",
    "    try {",
    '      const res = await fetch(`/api/sports/events/${eventId}`, { method: "DELETE" });',
    "      if (res.ok) {",
    "        await this.loadSportsDayEventsList();",
    '        this.showNotification("Acara sukan berjaya dipadam.", "success");',
    "      } else {",
    "        const err = await res.json().catch(() => ({}));",
    "        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal memadam acara sukan.' });",
    "      }",
    "    } catch (err) {",
    "      console.error(err);",
    "      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memadam acara sukan.' });",
    "    }",
    "  },"
]

lines[idx2_start:idx2_end + 1] = new_lines_2
print("Replaced 2: deleteSportsEvent")

# 3. prepareResultsFormForEvent delete button visibility
idx3 = None
for i, l in enumerate(lines):
    if "this.checkRecordBrokenPreview();" in l and any("prepareResultsFormForEvent" in lines[j] for j in range(max(0, i-60), i)):
        idx3 = i
        break
assert idx3 is not None, "idx3 not found"
new_lines_3 = [
    '      const btnDel = document.getElementById("btn-delete-event-results");',
    "      if (btnDel) {",
    "        if (this.canDelete() && existingRes.length > 0) {",
    '          btnDel.classList.remove("hidden");',
    "        } else {",
    '          btnDel.classList.add("hidden");',
    "        }",
    "      }",
    "",
    "      this.checkRecordBrokenPreview();"
]
lines[idx3:idx3+1] = new_lines_3
print("Replaced 3: prepareResultsFormForEvent button check")

# 4. deleteCurrentEventResults and deleteSportsEventResults
idx4_start = None
for i, l in enumerate(lines):
    if "async deleteCurrentEventResults() {" in l:
        idx4_start = i
        break
assert idx4_start is not None, "idx4_start not found"
idx4_end = idx4_start
while lines[idx4_end].strip() != "},":
    idx4_end += 1
idx4_end += 1
while lines[idx4_end].strip() != "},":
    idx4_end += 1

new_lines_4 = [
    "  async deleteCurrentEventResults() {",
    "    if (!this.canDelete()) {",
    "      Swal.fire({",
    "        icon: 'error',",
    "        title: 'Akses Ditolak',",
    "        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan acara. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',",
    "        confirmButtonColor: '#1e3a8a'",
    "      });",
    "      return;",
    "    }",
    '    const eventId = document.getElementById("results-event-select")?.value;',
    "    if (!eventId) {",
    "      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih acara sukan terlebih dahulu.' });",
    "      return;",
    "    }",
    "    await this.deleteSportsEventResults(eventId);",
    "  },",
    "",
    "  async deleteSportsEventResults(eventId) {",
    "    if (!this.canDelete()) {",
    "      Swal.fire({",
    "        icon: 'error',",
    "        title: 'Akses Ditolak',",
    "        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan acara. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',",
    "        confirmButtonColor: '#1e3a8a'",
    "      });",
    "      return;",
    "    }",
    "    const ev = (state.sportsEvents || []).find(e => e.id === Number(eventId));",
    "    const evName = ev ? ev.event_name : `Acara #${eventId}`;",
    "",
    "    const result = await Swal.fire({",
    "      title: 'Padam Keputusan Acara?',",
    "      text: `Adakah anda pasti ingin memadam keputusan bagi ${evName}? Tindakan ini akan mengosongkan rekod pemenang dan menukar status acara kembali kepada Pendaftaran.`,",
    "      icon: 'warning',",
    "      showCancelButton: true,",
    "      confirmButtonColor: '#dc2626',",
    "      cancelButtonColor: '#64748b',",
    "      confirmButtonText: 'Ya, Padam',",
    "      cancelButtonText: 'Batal'",
    "    });",
    "    if (!result.isConfirmed) return;",
    "",
    "    try {",
    "      const res = await fetch(`/api/sports/results/${eventId}`, {",
    '        method: "DELETE"',
    "      });",
    "      if (res.ok) {",
    "        this.showNotification(`Keputusan ${evName} berjaya dipadam!`, 'success');",
    "        await this.loadSportsDayEventsList();",
    "        await this.loadSportsDayOverview();",
    '        if (document.getElementById("results-event-select")?.value == eventId) {',
    "          await this.prepareResultsFormForEvent(eventId);",
    "        }",
    "      } else {",
    "        const err = await res.json().catch(() => ({}));",
    "        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal memadam keputusan acara sukan.' });",
    "      }",
    "    } catch (err) {",
    '      console.error("Delete sports event results error:", err);',
    "      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memadam keputusan acara.' });",
    "    }",
    "  },"
]

lines[idx4_start:idx4_end + 1] = new_lines_4
print("Replaced 4: deleteCurrentEventResults & deleteSportsEventResults")

# 5. Cross Country Overview Padam Button
idx5_start = None
for i, l in enumerate(lines):
    if "app.deleteCrossCountryCategoryResults('${cat.category_name}')" in l:
        idx5_start = i
        break
assert idx5_start is not None, "idx5_start not found"
idx5_end = idx5_start + 3  # up to </button>
assert "</button>" in lines[idx5_end], f"idx5_end mismatch: {lines[idx5_end]}"

new_lines_5 = [
    "                  ${this.canDelete() ? `",
    "                  <button onclick=\"app.deleteCrossCountryCategoryResults('${cat.category_name}')\" class=\"px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs\">",
    '                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>',
    "                    <span>Padam Keputusan</span>",
    "                  </button>",
    "                  ` : ''}"
]

lines[idx5_start:idx5_end + 1] = new_lines_5
print("Replaced 5: Cross Country Overview button")

# 6. deleteCrossCountryCategoryResults func
idx6_start = None
for i, l in enumerate(lines):
    if "async deleteCrossCountryCategoryResults(categoryName) {" in l:
        idx6_start = i
        break
assert idx6_start is not None, "idx6_start not found"
idx6_end = idx6_start
while lines[idx6_end].strip() != "},":
    idx6_end += 1

new_lines_6 = [
    "  async deleteCrossCountryCategoryResults(categoryName) {",
    "    if (!this.canDelete()) {",
    "      Swal.fire({",
    "        icon: 'error',",
    "        title: 'Akses Ditolak',",
    "        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',",
    "        confirmButtonColor: '#1e3a8a'",
    "      });",
    "      return;",
    "    }",
    "    if (!categoryName) {",
    '      const catSelect = document.getElementById("cc-record-category-select");',
    '      categoryName = catSelect ? catSelect.value : "Lelaki (Tahap 2)";',
    "    }",
    "    const confirmRes = await Swal.fire({",
    "      title: 'Padam Keputusan?',",
    "      text: `Adakah anda pasti ingin memadam SEMUA keputusan bagi Kategori: ${categoryName}? Tindakan ini akan mengosongkan rekod penamat dan mengira semula pungutan markah rumah sukan.`,",
    "      icon: 'warning',",
    "      showCancelButton: true,",
    "      confirmButtonColor: '#dc2626',",
    "      cancelButtonColor: '#64748b',",
    "      confirmButtonText: 'Ya, Padam',",
    "      cancelButtonText: 'Batal'",
    "    });",
    "    if (!confirmRes.isConfirmed) return;",
    "",
    "    try {",
    "      const res = await fetch(`/api/cross-country/results/${encodeURIComponent(categoryName)}`, {",
    '        method: "DELETE"',
    "      });",
    "      if (!res.ok) {",
    "        const errData = await res.json().catch(() => ({}));",
    "        Swal.fire({",
    "          icon: 'error',",
    "          title: 'Gagal Memadam',",
    '          text: errData.detail || "Gagal memadam keputusan.",',
    "          confirmButtonColor: '#1e3a8a'",
    "        });",
    "        return;",
    "      }",
    "      this.showNotification(`Keputusan bagi ${categoryName} berjaya dipadam!`, 'success');",
    '      this.closeModal("modal-record-cross-country");',
    "      await this.loadCrossCountryOverview();",
    "      await this.loadSportsDayOverview();",
    "    } catch (err) {",
    '      console.error("Delete cross country results error:", err);',
    "      Swal.fire({",
    "        icon: 'error',",
    "        title: 'Ralat',",
    '        text: "Ralat semasa memadam keputusan.",',
    "        confirmButtonColor: '#1e3a8a'",
    "      });",
    "    }",
    "  },"
]

lines[idx6_start:idx6_end + 1] = new_lines_6
print("Replaced 6: deleteCrossCountryCategoryResults func")

# 7. openRecordCrossCountryModal button visibility
idx7 = None
for i, l in enumerate(lines):
    if 'this.openModal("modal-record-cross-country");' in l:
        idx7 = i
        break
assert idx7 is not None, "idx7 not found"
new_lines_7 = [
    '    try {',
    '      this.openModal("modal-record-cross-country");',
    '      const btnDel = document.getElementById("btn-delete-crosscountry-modal");',
    '      if (btnDel) {',
    '        if (this.canDelete()) {',
    '          btnDel.classList.remove("hidden");',
    '        } else {',
    '          btnDel.classList.add("hidden");',
    '        }',
    '      }',
    '      this.switchCrossCountryInputTab("ind");'
]
lines[idx7-1:idx7+2] = new_lines_7
print("Replaced 7: openRecordCrossCountryModal")

with open(file_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write("\r\n".join(lines) + "\r\n")

print("SUCCESS: All 7 blocks updated in app.js!")
