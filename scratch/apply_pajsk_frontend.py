import re

APP_JS = "app/static/js/app.js"
with open(APP_JS, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add filterLetterOrgDropdown right before openNewPermissionLetterModal
filter_org_code = """
  filterLetterOrgDropdown(category) {
    const orgSelect = document.getElementById("let-form-org");
    if (!orgSelect) return;
    const orgs = (state.organizations || []).filter(o => !category || category === 'Lain-lain' || o.category === category);
    orgSelect.innerHTML = `<option value="">-- Pilihan Pasukan / Organisasi --</option>` +
      orgs.map(o => `<option value="${o.id}">${o.name} (${o.category})</option>`).join("");
  },

  async openNewPermissionLetterModal() {
"""

if "filterLetterOrgDropdown" not in content:
    content = content.replace("async openNewPermissionLetterModal() {", filter_org_code, 1)
    print("Added filterLetterOrgDropdown!")
else:
    print("filterLetterOrgDropdown already present")

# 2. Update openNewPermissionLetterModal to reset let-form-level, let-form-category, and populate let-form-org
old_new_modal = """    document.getElementById("let-form-transport").value = "Bas Sekolah Khas";
    document.getElementById("let-form-phone").value = state.schoolSettings?.phone || "05-8391234";"""

new_new_modal = """    document.getElementById("let-form-transport").value = "Bas Sekolah Khas";
    document.getElementById("let-form-phone").value = state.schoolSettings?.phone || "05-8391234";
    if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = "Daerah";
    if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = "Sukan & Permainan";
    this.filterLetterOrgDropdown("Sukan & Permainan");"""

if old_new_modal in content:
    content = content.replace(old_new_modal, new_new_modal, 1)
    print("Updated openNewPermissionLetterModal!")

# 3. Update openEditPermissionLetterModal to set let-form-level, let-form-category, let-form-org
old_edit_modal = """      document.getElementById("let-form-fee").value = letter.fee_amount || 0;
      document.getElementById("let-form-phone").value = letter.contact_phone || '';"""

new_edit_modal = """      document.getElementById("let-form-fee").value = letter.fee_amount || 0;
      document.getElementById("let-form-phone").value = letter.contact_phone || '';
      if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = letter.participation_level || "Daerah";
      if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = letter.activity_category || "Sukan & Permainan";
      this.filterLetterOrgDropdown(letter.activity_category || "Sukan & Permainan");
      if (document.getElementById("let-form-org")) document.getElementById("let-form-org").value = letter.represented_org_id || "";"""

if old_edit_modal in content:
    content = content.replace(old_edit_modal, new_edit_modal, 1)
    print("Updated openEditPermissionLetterModal!")

# 4. Update savePermissionLetter payload & reload
old_save_payload = """      fee_amount: parseFloat(document.getElementById("let-form-fee").value) || 0.0,
      contact_phone: document.getElementById("let-form-phone").value.trim() || state.schoolSettings?.phone || "05-8391234",
      student_ids: checked
    };"""

new_save_payload = """      fee_amount: parseFloat(document.getElementById("let-form-fee").value) || 0.0,
      contact_phone: document.getElementById("let-form-phone").value.trim() || state.schoolSettings?.phone || "05-8391234",
      participation_level: document.getElementById("let-form-level")?.value || "Daerah",
      activity_category: document.getElementById("let-form-category")?.value || "Sukan & Permainan",
      represented_org_id: parseInt(document.getElementById("let-form-org")?.value) || null,
      student_ids: checked
    };"""

if old_save_payload in content:
    content = content.replace(old_save_payload, new_save_payload, 1)
    print("Updated savePermissionLetter payload!")

old_save_reload = """        this.closeModal("modal-permission-letter");
        Swal.fire({ icon: 'success', title: 'Berjaya', text: id ? 'Surat kebenaran berjaya dikemas kini!' : `Surat kebenaran rasmi untuk ${checked.length} murid berjaya dijana!`, timer: 2000, showConfirmButton: false });
        this.loadPermissionLetters();"""

new_save_reload = """        this.closeModal("modal-permission-letter");
        Swal.fire({ icon: 'success', title: 'Berjaya', text: id ? 'Surat kebenaran berjaya dikemas kini!' : `Surat kebenaran rasmi untuk ${checked.length} murid berjaya dijana!`, timer: 2000, showConfirmButton: false });
        this.loadPermissionLetters();
        this.loadExternalEvents();
        this.loadStudentPajskAchievements();"""

if old_save_reload in content:
    content = content.replace(old_save_reload, new_save_reload, 1)
    print("Updated savePermissionLetter reload!")

# 5. Add applyBatchPajskAchievement, openEditExternalEventModal, deleteExternalEvent
methods_to_add = """
  applyBatchPajskAchievement() {
    const batchVal = document.getElementById("pajsk-batch-achievement")?.value || "Penyertaan";
    if (!state.currentPajskStudents || state.currentPajskStudents.length === 0) {
      Swal.fire({ icon: 'info', title: 'Perhatian', text: 'Tiada murid dalam senarai kontinjen untuk ditetapkan.' });
      return;
    }
    state.currentPajskStudents.forEach(item => {
      item.achievement = batchVal;
    });
    this.renderPajskModalStudentsTable();
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: 'success',
      title: `Pencapaian '${batchVal}' ditetapkan kepada semua ${state.currentPajskStudents.length} murid!`,
      showConfirmButton: false,
      timer: 2000
    });
  },

  async openEditExternalEventModal(eventId) {
    try {
      const res = await fetch(`/api/pajsk/events/${eventId}`);
      if (!res.ok) return;
      const ev = await res.json();

      const modal = document.getElementById("modal-external-event");
      document.getElementById("modal-pajsk-title").textContent = `Kemaskini Pertandingan & Pencapaian PAJSK: ${ev.program_name}`;
      document.getElementById("pajsk-form-id").value = ev.id;
      document.getElementById("pajsk-form-program").value = ev.program_name || "";
      document.getElementById("pajsk-form-date").value = ev.event_date || "";
      document.getElementById("pajsk-form-level").value = ev.participation_level || "Daerah";
      document.getElementById("pajsk-form-category").value = ev.activity_category || "Sukan & Permainan";
      document.getElementById("pajsk-form-venue").value = ev.venue || "";
      document.getElementById("pajsk-form-organizer").value = ev.organizer || "";

      const orgSelect = document.getElementById("pajsk-form-org");
      if (orgSelect) {
        orgSelect.innerHTML = `<option value="">-- Pilihan Organisasi --</option>` +
          (state.organizations || []).map(o => `<option value="${o.id}" ${o.id === ev.represented_org_id ? 'selected' : ''}>${o.name}</option>`).join("");
      }

      state.currentPajskStudents = (ev.students || []).map(st => ({
        student_id: st.student_id,
        role: st.role || "Peserta",
        achievement: st.achievement || "Penyertaan",
        remarks: st.remarks || ""
      }));

      if (state.currentPajskStudents.length === 0) {
        this.addStudentRowToPajskModal();
      } else {
        this.renderPajskModalStudentsTable();
      }

      modal.classList.remove("hidden");
      lucide.createIcons();
    } catch (err) {
      console.error("openEditExternalEventModal error:", err);
    }
  },

  async deleteExternalEvent(eventId, name) {
    if (!this.canDelete()) {
      Swal.fire({
        icon: 'error',
        title: 'Akses Ditolak',
        text: 'Hanya akaun pentadbir dan pengurusan (Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan) dibenarkan memadam rekod pertandingan luar.',
        confirmButtonColor: '#1e3a8a'
      });
      return;
    }

    const result = await Swal.fire({
      title: 'Padam Rekod Pertandingan?',
      text: `Adakah anda pasti mahu memadam rekod "${name}" ini? Semua rekod pencapaian dan markah PAJSK bagi murid kontinjen ini akan dikeluarkan.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#64748b',
      confirmButtonText: 'Ya, Padam!',
      cancelButtonText: 'Batal'
    });

    if (!result.isConfirmed) return;

    try {
      const res = await fetch(`/api/pajsk/events/${eventId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        this.showNotification("Rekod pertandingan berjaya dipadamkan.", "success");
        await this.loadExternalEvents();
        await this.loadStudentPajskAchievements();
        await this.loadDashboard();
      } else {
        const err = await res.json().catch(() => ({}));
        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal memadam rekod pertandingan.' });
      }
    } catch (err) {
      console.error("deleteExternalEvent error:", err);
      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat sambungan pelayan.' });
    }
  },
"""

if "applyBatchPajskAchievement" not in content:
    content = content.replace("openNewExternalEventModal() {", methods_to_add + "\n  openNewExternalEventModal() {", 1)
    print("Added PAJSK methods!")

# 6. Update saveExternalEvent to support PUT when pajsk-form-id is present
old_save_ext = """  async saveExternalEvent(e) {
    e.preventDefault();
    if (state.currentPajskStudents.length === 0) {
      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila masukkan sekurang-kurangnya seorang murid.' });
      return;
    }

    const payload = {
      program_name: document.getElementById("pajsk-form-program").value.trim(),
      event_date: document.getElementById("pajsk-form-date").value,
      venue: document.getElementById("pajsk-form-venue").value.trim(),
      organizer: document.getElementById("pajsk-form-organizer").value.trim(),
      activity_category: document.getElementById("pajsk-form-category").value,
      participation_level: document.getElementById("pajsk-form-level").value,
      represented_org_id: parseInt(document.getElementById("pajsk-form-org").value) || null,
      students: state.currentPajskStudents
    };

    try {
      const res = await fetch("/api/pajsk/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        this.closeModal("modal-external-event");
        Swal.fire({ icon: 'success', title: 'Berjaya', text: 'Penyertaan luar dan markah PAJSK berjaya direkodkan!', timer: 2000, showConfirmButton: false });
        this.loadExternalEvents();
        this.loadDashboard();
      }
    } catch (err) {
      console.error(err);
    }
  },"""

new_save_ext = """  async saveExternalEvent(e) {
    e.preventDefault();
    if (state.currentPajskStudents.length === 0) {
      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila masukkan sekurang-kurangnya seorang murid.' });
      return;
    }

    const formId = document.getElementById("pajsk-form-id")?.value;
    const payload = {
      program_name: document.getElementById("pajsk-form-program").value.trim(),
      event_date: document.getElementById("pajsk-form-date").value,
      venue: document.getElementById("pajsk-form-venue").value.trim(),
      organizer: document.getElementById("pajsk-form-organizer").value.trim(),
      activity_category: document.getElementById("pajsk-form-category").value,
      participation_level: document.getElementById("pajsk-form-level").value,
      represented_org_id: parseInt(document.getElementById("pajsk-form-org").value) || null,
      students: state.currentPajskStudents
    };

    try {
      let res;
      if (formId) {
        res = await fetch(`/api/pajsk/events/${formId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch("/api/pajsk/events", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      if (res.ok) {
        this.closeModal("modal-external-event");
        Swal.fire({
          icon: 'success',
          title: 'Berjaya',
          text: formId ? 'Pencapaian murid & skor PAJSK berjaya dikemas kini!' : 'Penyertaan luar dan markah PAJSK berjaya direkodkan!',
          timer: 2000,
          showConfirmButton: false
        });
        await this.loadExternalEvents();
        await this.loadStudentPajskAchievements();
        await this.loadDashboard();
      } else {
        const err = await res.json().catch(() => ({}));
        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal menyimpan rekod PAJSK.' });
      }
    } catch (err) {
      console.error(err);
      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat sambungan pelayan.' });
    }
  },"""

if old_save_ext in content:
    content = content.replace(old_save_ext, new_save_ext, 1)
    print("Updated saveExternalEvent!")

# 7. Update loadExternalEvents actions column (Edit + Delete button with canDelete())
old_ext_table_actions = """          <td class="p-3.5 text-center">
            <div class="flex items-center justify-center space-x-1.5">
              <button onclick="app.prepareReport('student_achievements')" title="Cetak Keputusan" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg">
                <i data-lucide="printer" class="w-4 h-4"></i>
              </button>
            </div>
          </td>"""

new_ext_table_actions = """          <td class="p-3.5 text-center">
            <div class="flex items-center justify-center space-x-1.5">
              <button onclick="app.openEditExternalEventModal(${ev.id})" title="Kemaskini Pencapaian & Skor Murid" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg">
                <i data-lucide="edit-3" class="w-4 h-4"></i>
              </button>
              <button onclick="app.prepareReport('student_achievements')" title="Cetak Keputusan" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg">
                <i data-lucide="printer" class="w-4 h-4"></i>
              </button>
              ${this.canDelete() ? `
              <button onclick="app.deleteExternalEvent(${ev.id}, '${(ev.program_name || '').replace(/'/g, "\\\\\'")}')" title="Padam Rekod Pertandingan" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
              ` : ''}
            </div>
          </td>"""

if old_ext_table_actions in content:
    content = content.replace(old_ext_table_actions, new_ext_table_actions, 1)
    print("Updated loadExternalEvents table actions!")

with open(APP_JS, "w", encoding="utf-8") as f:
    f.write(content)
print("Saved changes to app.js!")
