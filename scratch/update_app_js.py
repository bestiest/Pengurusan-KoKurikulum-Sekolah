import os

js_path = r"C:\Antigravity\Sistem Pengurusan Unit Kokurikulum\app\static\js\app.js"

with open(js_path, "r", encoding="utf-8") as f:
    content = f.read()

# Normalize to \n
c = content.replace("\r\n", "\n")

# 1. Sports Day Events Table Buttons
target1 = """            ${ev.status === 'Selesai' ? `
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

replace1 = """            ${(ev.status === 'Selesai' && this.canDelete()) ? `
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

assert target1 in c, "target1 not found"
c = c.replace(target1, replace1)

# 2. deleteSportsEvent
target2 = """  async deleteSportsEvent(eventId) {
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

replace2 = """  async deleteSportsEvent(eventId) {
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

assert target2 in c, "target2 not found"
c = c.replace(target2, replace2)

# 3. deleteCurrentEventResults & deleteSportsEventResults
target3 = """  async deleteCurrentEventResults() {
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

replace3 = """  async deleteCurrentEventResults() {
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

assert target3 in c, "target3 not found"
c = c.replace(target3, replace3)

# 4. Cross Country Overview Padam Button
target4 = """                  <button onclick="app.deleteCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    <span>Padam Keputusan</span>
                  </button>"""

replace4 = """                  ${this.canDelete() ? `
                  <button onclick="app.deleteCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    <span>Padam Keputusan</span>
                  </button>
                  ` : ''}"""

assert target4 in c, "target4 not found"
c = c.replace(target4, replace4)

# 5. deleteCrossCountryCategoryResults
target5 = """  async deleteCrossCountryCategoryResults(categoryName) {
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

replace5 = """  async deleteCrossCountryCategoryResults(categoryName) {
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

assert target5 in c, "target5 not found"
c = c.replace(target5, replace5)

# Write back with CRLF
with open(js_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(c)

print("Successfully updated app.js with all 5 targets!")
