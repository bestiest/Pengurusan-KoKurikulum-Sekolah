with open("app/static/js/app.js", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update openNewPermissionLetterModal
target1 = 'document.getElementById("let-form-phone").value = state.schoolSettings?.phone || "05-8391234";'
replacement1 = """document.getElementById("let-form-phone").value = state.schoolSettings?.phone || "05-8391234";
    if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = "Daerah";
    if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = "Sukan & Permainan";
    this.filterLetterOrgDropdown("Sukan & Permainan");"""

if target1 in text:
    text = text.replace(target1, replacement1, 1)
    print("1. Updated openNewPermissionLetterModal successfully!")
else:
    print("1. target1 not found")

# 2. Update openEditPermissionLetterModal
target2 = """      document.getElementById("let-form-fee").value = letter.fee_amount || 0;



      document.getElementById("let-form-phone").value = letter.contact_phone || '';"""

replacement2 = """      document.getElementById("let-form-fee").value = letter.fee_amount || 0;
      document.getElementById("let-form-phone").value = letter.contact_phone || '';
      if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = letter.participation_level || "Daerah";
      if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = letter.activity_category || "Sukan & Permainan";
      this.filterLetterOrgDropdown(letter.activity_category || "Sukan & Permainan");
      if (document.getElementById("let-form-org")) document.getElementById("let-form-org").value = letter.represented_org_id || "";"""

if target2 in text:
    text = text.replace(target2, replacement2, 1)
    print("2. Updated openEditPermissionLetterModal successfully!")
else:
    print("2. target2 not found")

# 3. Update savePermissionLetter
target3 = """      fee_amount: parseFloat(document.getElementById("let-form-fee").value) || 0.0,



      contact_phone: document.getElementById("let-form-phone").value.trim() || state.schoolSettings?.phone || "05-8391234",



      student_ids: checked"""

replacement3 = """      fee_amount: parseFloat(document.getElementById("let-form-fee").value) || 0.0,
      contact_phone: document.getElementById("let-form-phone").value.trim() || state.schoolSettings?.phone || "05-8391234",
      participation_level: document.getElementById("let-form-level")?.value || "Daerah",
      activity_category: document.getElementById("let-form-category")?.value || "Sukan & Permainan",
      represented_org_id: parseInt(document.getElementById("let-form-org")?.value) || null,
      student_ids: checked"""

if target3 in text:
    text = text.replace(target3, replacement3, 1)
    print("3. Updated savePermissionLetter payload successfully!")
else:
    print("3. target3 not found")

target4 = """        this.closeModal("modal-permission-letter");



        Swal.fire({ icon: 'success', title: 'Berjaya', text: id ? 'Surat kebenaran berjaya dikemas kini!' : `Surat kebenaran rasmi untuk ${checked.length} murid berjaya dijana!`, timer: 2000, showConfirmButton: false });



        this.loadPermissionLetters();"""

replacement4 = """        this.closeModal("modal-permission-letter");
        Swal.fire({ icon: 'success', title: 'Berjaya', text: id ? 'Surat kebenaran berjaya dikemas kini!' : `Surat kebenaran rasmi untuk ${checked.length} murid berjaya dijana!`, timer: 2000, showConfirmButton: false });
        this.loadPermissionLetters();
        this.loadExternalEvents();
        this.loadStudentPajskAchievements();"""

if target4 in text:
    text = text.replace(target4, replacement4, 1)
    print("4. Updated savePermissionLetter reload successfully!")
else:
    print("4. target4 not found")

# 5. Update saveExternalEvent to support PUT and auto-refresh
target5 = """  async saveExternalEvent(e) {



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

replacement5 = """  async saveExternalEvent(e) {
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

if target5 in text:
    text = text.replace(target5, replacement5, 1)
    print("5. Updated saveExternalEvent successfully!")
else:
    print("5. target5 not found")

# 6. Update loadExternalEvents actions column (Edit + Delete button)
target6 = """          <td class="p-3.5 text-center">



            <div class="flex items-center justify-center space-x-1.5">



              <button onclick="app.prepareReport('student_achievements')" title="Cetak Keputusan" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg">



                <i data-lucide="printer" class="w-4 h-4"></i>



              </button>



            </div>



          </td>"""

replacement6 = """          <td class="p-3.5 text-center">
            <div class="flex items-center justify-center space-x-1.5">
              <button onclick="app.openEditExternalEventModal(${ev.id})" title="Kemaskini Pencapaian & Skor Murid" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg transition">
                <i data-lucide="edit-3" class="w-4 h-4"></i>
              </button>
              <button onclick="app.prepareReport('student_achievements')" title="Cetak Keputusan" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg transition">
                <i data-lucide="printer" class="w-4 h-4"></i>
              </button>
              ${this.canDelete() ? `
              <button onclick="app.deleteExternalEvent(${ev.id}, '${(ev.program_name || '').replace(/'/g, "\\\\\'")}')" title="Padam Rekod Pertandingan" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg transition">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
              ` : ''}
            </div>
          </td>"""

if target6 in text:
    text = text.replace(target6, replacement6, 1)
    print("6. Updated loadExternalEvents actions column successfully!")
else:
    print("6. target6 not found")

with open("app/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(text)
print("Saved all changes to app.js!")
