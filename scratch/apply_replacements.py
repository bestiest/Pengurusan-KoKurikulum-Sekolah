import sys

file_path = r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js"

with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Normalize line endings to \n
content = text.replace("\r\n", "\n")

# 1. Sports Day Events Table Buttons
anchor1_old = """            ${ev.status === 'Selesai' ? `
            <button onclick="app.deleteSportsEventResults(${ev.id})" title="Padam Keputusan Acara" class="p-1.5 bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-lg transition">
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
            </button>
            ` : ''}
            <button onclick="app.openAddSportsEventModal(${ev.id})" title="Kemaskini Acara" class="p-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg transition">
              <i data-lucide="edit" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="app.deleteSportsEvent(${ev.id})" title="Padam Acara" class="p-1.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>"""

anchor1_new = """            ${(ev.status === 'Selesai' && this.canDelete()) ? `
            <button onclick="app.deleteSportsEventResults(${ev.id})" title="Padam Keputusan Acara" class="p-1.5 bg-rose-50 text-rose-600 hover:bg-rose-100 rounded-lg transition">
              <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i>
            </button>
            ` : ''}
            <button onclick="app.openAddSportsEventModal(${ev.id})" title="Kemaskini Acara" class="p-1.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg transition">
              <i data-lucide="edit" class="w-3.5 h-3.5"></i>
            </button>
            ${this.canDelete() ? `
            <button onclick="app.deleteSportsEvent(${ev.id})" title="Padam Acara" class="p-1.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
            ` : ''}"""

# 2. deleteSportsEvent
anchor2_old = """  async deleteSportsEvent(eventId) {
    if (!confirm("Adakah anda pasti ingin memadam acara sukan ini berserta rekod keputusannya?")) return;
    try {
      const res = await fetch(`/api/sports/events/${eventId}`, { method: "DELETE" });
      if (res.ok) {
        await this.loadSportsDayEventsList();
        this.showToast("Acara sukan berjaya dipadam.");
      }
    } catch (err) {
      console.error(err);
    }
  },"""

anchor2_new = """  async deleteSportsEvent(eventId) {
    if (!this.canDelete()) {
      Swal.fire({
        icon: 'error',
        title: 'Akses Ditolak',
        text: 'Anda tidak mempunyai kebenaran untuk memadam acara sukan. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',
        confirmButtonColor: '#1e3a8a'
      });
      return;
    }
    const result = await Swal.fire({
      title: 'Padam Acara Sukan?',
      text: 'Adakah anda pasti ingin memadam acara sukan ini berserta rekod keputusannya?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#64748b',
      confirmButtonText: 'Ya, Padam',
      cancelButtonText: 'Batal'
    });
    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`/api/sports/events/${eventId}`, { method: "DELETE" });
      if (res.ok) {
        await this.loadSportsDayEventsList();
        this.showNotification("Acara sukan berjaya dipadam.", "success");
      } else {
        const err = await res.json().catch(() => ({}));
        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal memadam acara sukan.' });
      }
    } catch (err) {
      console.error(err);
      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memadam acara sukan.' });
    }
  },"""

# 3. prepareResultsFormForEvent (hide/show delete button)
anchor3_old = """      this.checkRecordBrokenPreview();
    } catch (err) {"""

anchor3_new = """      const btnDel = document.getElementById("btn-delete-event-results");
      if (btnDel) {
        if (this.canDelete() && existingRes.length > 0) {
          btnDel.classList.remove("hidden");
        } else {
          btnDel.classList.add("hidden");
        }
      }

      this.checkRecordBrokenPreview();
    } catch (err) {"""

# 4. deleteCurrentEventResults and deleteSportsEventResults
anchor4_old = """  async deleteCurrentEventResults() {
    const eventId = document.getElementById("results-event-select")?.value;
    if (!eventId) {
      alert("Sila pilih acara sukan terlebih dahulu.");
      return;
    }
    await this.deleteSportsEventResults(eventId);
  },

  async deleteSportsEventResults(eventId) {
    const ev = (state.sportsEvents || []).find(e => e.id === Number(eventId));
    const evName = ev ? ev.event_name : `Acara #${eventId}`;

    if (!confirm(`Adakah anda pasti ingin memadam keputusan bagi ${evName}?
\\nTindakan ini akan mengosongkan rekod pemenang dan menukar status acara kembali kepada Pendaftaran.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/sports/results/${eventId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        this.showNotification(`Keputusan ${evName} berjaya dipadam!`, "success");
        await this.loadSportsDayEventsList();
        await this.loadSportsDayOverview();
        if (document.getElementById("results-event-select")?.value == eventId) {
          await this.prepareResultsFormForEvent(eventId);
        }
      } else {
        alert("Gagal memadam keputusan acara sukan.");
      }
    } catch (err) {
      console.error("Delete sports event results error:", err);
      alert("Ralat semasa memadam keputusan acara.");
    }
  },"""

# Note: In original content, line 5217 had "\n\nTindakan ini..."
# Let's verify how it was formatted in inspect_lines:
# 5217:     if (!confirm(`Adakah anda pasti ingin memadam keputusan bagi ${evName}?\n\nTindakan ini akan mengosongkan rekod pemenang dan menukar status acara kembali kepada Pendaftaran.`)) {

anchor4_old_exact = """  async deleteCurrentEventResults() {
    const eventId = document.getElementById("results-event-select")?.value;
    if (!eventId) {
      alert("Sila pilih acara sukan terlebih dahulu.");
      return;
    }
    await this.deleteSportsEventResults(eventId);
  },

  async deleteSportsEventResults(eventId) {
    const ev = (state.sportsEvents || []).find(e => e.id === Number(eventId));
    const evName = ev ? ev.event_name : `Acara #${eventId}`;

    if (!confirm(`Adakah anda pasti ingin memadam keputusan bagi ${evName}?\\n\\nTindakan ini akan mengosongkan rekod pemenang dan menukar status acara kembali kepada Pendaftaran.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/sports/results/${eventId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        this.showNotification(`Keputusan ${evName} berjaya dipadam!`, "success");
        await this.loadSportsDayEventsList();
        await this.loadSportsDayOverview();
        if (document.getElementById("results-event-select")?.value == eventId) {
          await this.prepareResultsFormForEvent(eventId);
        }
      } else {
        alert("Gagal memadam keputusan acara sukan.");
      }
    } catch (err) {
      console.error("Delete sports event results error:", err);
      alert("Ralat semasa memadam keputusan acara.");
    }
  },"""

anchor4_new = """  async deleteCurrentEventResults() {
    if (!this.canDelete()) {
      Swal.fire({
        icon: 'error',
        title: 'Akses Ditolak',
        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan acara. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',
        confirmButtonColor: '#1e3a8a'
      });
      return;
    }
    const eventId = document.getElementById("results-event-select")?.value;
    if (!eventId) {
      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih acara sukan terlebih dahulu.' });
      return;
    }
    await this.deleteSportsEventResults(eventId);
  },

  async deleteSportsEventResults(eventId) {
    if (!this.canDelete()) {
      Swal.fire({
        icon: 'error',
        title: 'Akses Ditolak',
        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan acara. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',
        confirmButtonColor: '#1e3a8a'
      });
      return;
    }
    const ev = (state.sportsEvents || []).find(e => e.id === Number(eventId));
    const evName = ev ? ev.event_name : `Acara #${eventId}`;

    const result = await Swal.fire({
      title: 'Padam Keputusan Acara?',
      text: `Adakah anda pasti ingin memadam keputusan bagi ${evName}? Tindakan ini akan mengosongkan rekod pemenang dan menukar status acara kembali kepada Pendaftaran.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#64748b',
      confirmButtonText: 'Ya, Padam',
      cancelButtonText: 'Batal'
    });
    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`/api/sports/results/${eventId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        this.showNotification(`Keputusan ${evName} berjaya dipadam!`, "success");
        await this.loadSportsDayEventsList();
        await this.loadSportsDayOverview();
        if (document.getElementById("results-event-select")?.value == eventId) {
          await this.prepareResultsFormForEvent(eventId);
        }
      } else {
        const err = await res.json().catch(() => ({}));
        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal memadam keputusan acara sukan.' });
      }
    } catch (err) {
      console.error("Delete sports event results error:", err);
      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memadam keputusan acara.' });
    }
  },"""

# 5. Cross Country Overview Padam Button
anchor5_old = """                  <button onclick="app.deleteCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    <span>Padam Keputusan</span>
                  </button>"""

anchor5_new = """                  ${this.canDelete() ? `
                  <button onclick="app.deleteCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    <span>Padam Keputusan</span>
                  </button>
                  ` : ''}"""

# 6. deleteCrossCountryCategoryResults function
anchor6_old = """  async deleteCrossCountryCategoryResults(categoryName) {
    if (!categoryName) {
      const catSelect = document.getElementById("cc-record-category-select");
      categoryName = catSelect ? catSelect.value : "Lelaki (Tahap 2)";
    }
    if (!confirm(`Adakah anda pasti ingin memadam SEMUA keputusan bagi Kategori: ${categoryName}?\\n\\nTindakan ini akan mengosongkan rekod penamat dan mengira semula pungutan markah rumah sukan.`)) {
      return;
    }
    try {
      const res = await fetch(`/api/cross-country/results/${encodeURIComponent(categoryName)}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        alert("Gagal memadam keputusan.");
        return;
      }
      this.showNotification(`Keputusan bagi ${categoryName} berjaya dipadam!`, "success");
      this.closeModal("modal-record-cross-country");
      await this.loadCrossCountryOverview();
      await this.loadSportsDayOverview();
    } catch (err) {
      console.error("Delete cross country results error:", err);
      alert("Ralat semasa memadam keputusan.");
    }
  },"""

anchor6_new = """  async deleteCrossCountryCategoryResults(categoryName) {
    if (!this.canDelete()) {
      Swal.fire({
        icon: 'error',
        title: 'Akses Ditolak',
        text: 'Anda tidak mempunyai kebenaran untuk memadam keputusan. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',
        confirmButtonColor: '#1e3a8a'
      });
      return;
    }
    if (!categoryName) {
      const catSelect = document.getElementById("cc-record-category-select");
      categoryName = catSelect ? catSelect.value : "Lelaki (Tahap 2)";
    }
    const confirmRes = await Swal.fire({
      title: 'Padam Keputusan?',
      text: `Adakah anda pasti ingin memadam SEMUA keputusan bagi Kategori: ${categoryName}? Tindakan ini akan mengosongkan rekod penamat dan mengira semula pungutan markah rumah sukan.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#64748b',
      confirmButtonText: 'Ya, Padam',
      cancelButtonText: 'Batal'
    });
    if (!confirmRes.isConfirmed) return;

    try {
      const res = await fetch(`/api/cross-country/results/${encodeURIComponent(categoryName)}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        Swal.fire({
          icon: 'error',
          title: 'Gagal Memadam',
          text: errData.detail || "Gagal memadam keputusan.",
          confirmButtonColor: '#1e3a8a'
        });
        return;
      }
      this.showNotification(`Keputusan bagi ${categoryName} berjaya dipadam!`, "success");
      this.closeModal("modal-record-cross-country");
      await this.loadCrossCountryOverview();
      await this.loadSportsDayOverview();
    } catch (err) {
      console.error("Delete cross country results error:", err);
      Swal.fire({
        icon: 'error',
        title: 'Ralat',
        text: "Ralat semasa memadam keputusan.",
        confirmButtonColor: '#1e3a8a'
      });
    }
  },"""

# 7. openRecordCrossCountryModal (hide/show delete button)
anchor7_old = """  async openRecordCrossCountryModal() {
    try {
      this.openModal("modal-record-cross-country");
      this.switchCrossCountryInputTab("ind");"""

anchor7_new = """  async openRecordCrossCountryModal() {
    try {
      this.openModal("modal-record-cross-country");
      const btnDel = document.getElementById("btn-delete-crosscountry-modal");
      if (btnDel) {
        if (this.canDelete()) {
          btnDel.classList.remove("hidden");
        } else {
          btnDel.classList.add("hidden");
        }
      }
      this.switchCrossCountryInputTab("ind");"""

replacements = [
    ("Anchor 1 (Sports event buttons)", anchor1_old, anchor1_new),
    ("Anchor 2 (deleteSportsEvent)", anchor2_old, anchor2_new),
    ("Anchor 3 (prepareResultsFormForEvent)", anchor3_old, anchor3_new),
    ("Anchor 4 (deleteCurrentEventResults & deleteSportsEventResults)", anchor4_old_exact, anchor4_new),
    ("Anchor 5 (Cross Country Overview Padam Button)", anchor5_old, anchor5_new),
    ("Anchor 6 (deleteCrossCountryCategoryResults)", anchor6_old, anchor6_new),
    ("Anchor 7 (openRecordCrossCountryModal)", anchor7_old, anchor7_new),
]

for name, old_s, new_s in replacements:
    if old_s in content:
        content = content.replace(old_s, new_s)
        print(f"SUCCESS: {name}")
    else:
        print(f"FAILED to find: {name}")
        sys.exit(1)

with open(file_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(content)

print("All replacements successfully applied to app.js!")
