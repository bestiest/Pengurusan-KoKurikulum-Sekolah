/**



 * SISTEM PENGURUSAN UNIT KOKURIKULUM



 * SEKOLAH KEBANGSAAN SUNGAI DENDANG (ABA6034)



 * Frontend Single Page Application Controller



 */







const state = {



  currentUser: null,



  activeRole: "Admin",



  currentView: "dashboard",



  schoolSettings: {},



  classes: [],



  teachers: [],



  organizations: [],



  students: [],



  selectedStudentIds: new Set(),



  currentOrgTab: "all",



  charts: {



    levels: null,



    houses: null



  },



  currentManagingOrgId: null,



  currentManagingOrg: null,



  addMemberSelectedStudentIds: new Set(),



  selectedLetterTeachers: [],



  currentAttendanceStudents: [],



  currentPajskStudents: [],



  sportsActiveSubTab: "standings",



  sportsEvents: [],



  sportsSelectedHouseId: null,



  sportsHouseEnrollmentData: null,



  sportsSelectedEventId: null,



  sportsCurrentStartListData: null,



  sportsOverallData: null



};







const app = {



  canDelete() {



    const role = (state.activeRole || state.currentUser?.role || "").toLowerCase().replace(/[\s_]/g, "");



    if (!role) return false;



    // Strictly block Guru Penasihat and Guru Pemimpin from deleting anything



    if (role.includes("gurupenasihat") || role.includes("gurupemimpin")) {



      return false;



    }



    const allowed = [



      "admin",



      "gpk",



      "gpkkokurikulum",



      "gpkkoko",



      "penyelaras",



      "penyelaraskokurikulum",



      "setiausahasukan",



      "susukan",



      "setiausahakokurikulum",



      "sukoko"



    ];



    return allowed.some(a => role === a || role.includes(a) || a.includes(role));



  },







  showNotification(msg, type = "success") {



    if (typeof Swal !== "undefined") {



      const Toast = Swal.mixin({



        toast: true,



        position: 'top-end',



        showConfirmButton: false,



        timer: 3000,



        timerProgressBar: true,



        didOpen: (toast) => {



          toast.addEventListener('mouseenter', Swal.stopTimer);



          toast.addEventListener('mouseleave', Swal.resumeTimer);



        }



      });



      Toast.fire({



        icon: type,



        title: msg



      });



    } else {



      alert(msg);



    }



  },







  // ==========================================



  // INITIALIZATION & AUTH



  // ==========================================



  async init() {



    try {



      await this.fetchSchoolSettings();



      



      // Check if active session exists in current browser tab



      const isSessionActive = sessionStorage.getItem("koko_session_active") === "true";



      if (!isSessionActive) {



        this.showLoginView();



        return;



      }







      const loggedIn = await this.fetchCurrentUser();



      if (!loggedIn) {



        sessionStorage.removeItem("koko_session_active");



        this.showLoginView();



        return;



      }







      this.hideLoginView();



      await this.fetchClasses();



      await this.fetchTeachers();



      await this.fetchOrganizations();



      await this.ensureStudentsLoaded();



      



      this.initRouting();



      this.navigate(window.location.hash.replace("#", "") || "dashboard");



      lucide.createIcons();



    } catch (err) {



      console.error("Initialization Error:", err);



      this.showLoginView();



    }



  },







  showLoginView() {



    state.currentUser = null;



    const appWorkspace = document.getElementById("app-workspace");



    const topNavbar = document.getElementById("top-navbar");



    const sidebar = document.getElementById("sidebar");



    const viewLogin = document.getElementById("view-login");



    



    if (appWorkspace) appWorkspace.classList.add("hidden");



    if (topNavbar) topNavbar.classList.add("hidden");



    if (sidebar) sidebar.classList.add("hidden");



    



    const views = ["dashboard", "students", "organizations", "attendance", "activities", "permission", "pajsk", "sports-day", "cross-country", "reports", "settings"];



    views.forEach(v => {



      const el = document.getElementById(`view-${v}`);



      if (el) el.classList.add("hidden");



    });







    if (viewLogin) viewLogin.classList.remove("hidden");



    



    // Clear URL hash to prevent any routing to dashboard while logged out



    if (window.location.hash) {



      history.replaceState(null, "", window.location.pathname);



    }



    



    this.fetchActiveUsernamesForLogin();



    lucide.createIcons();



  },







  hideLoginView() {



    const appWorkspace = document.getElementById("app-workspace");



    const topNavbar = document.getElementById("top-navbar");



    const sidebar = document.getElementById("sidebar");



    const viewLogin = document.getElementById("view-login");



    



    if (viewLogin) viewLogin.classList.add("hidden");



    if (appWorkspace) appWorkspace.classList.remove("hidden");



    if (topNavbar) topNavbar.classList.remove("hidden");



    if (sidebar) sidebar.classList.remove("hidden");



    lucide.createIcons();



  },







  async fetchCurrentUser() {



    try {



      const res = await fetch("/api/auth/me");



      if (res.ok) {



        const data = await res.json();



        state.currentUser = data.user;



        state.activeRole = state.currentUser.role;



        this.updateUserUI();



        return true;



      } else {



        state.currentUser = null;



        return false;



      }



    } catch (e) {



      state.currentUser = null;



      return false;



    }



  },







  updateUserUI() {



    const roleSelector = document.getElementById("role-selector");



    if (roleSelector) roleSelector.value = state.activeRole;







    const initials = state.currentUser?.full_name?.split(" ").map(n => n[0]).slice(0, 2).join("") || "AD";



    const avatarEl = document.getElementById("user-avatar-initials");



    if (avatarEl) avatarEl.textContent = initials.toUpperCase();



    



    const nameEl = document.getElementById("user-display-name");



    if (nameEl) nameEl.textContent = state.currentUser?.full_name || "Pentadbir Sistem";



    



    const badgeEl = document.getElementById("user-role-badge");



    if (badgeEl) badgeEl.textContent = state.activeRole;



  },







  async handleLoginFormSubmit(e) {



    if (e) e.preventDefault();



    const usernameInput = document.getElementById("login-username");



    const passwordInput = document.getElementById("login-password");



    const username = usernameInput ? usernameInput.value.trim() : "";



    const password = passwordInput ? passwordInput.value : "";



    



    if (!username || !password) {



      Swal.fire({



        icon: 'warning',



        title: 'Maklumat Diperlukan',



        text: 'Sila masukkan ID Pengguna dan Kata Laluan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }







    try {



      const res = await fetch("/api/auth/login", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ username, password })



      });



      const data = await res.json();



      if (!res.ok) {



        Swal.fire({



          icon: 'error',



          title: 'Gagal Log Masuk',



          text: data.detail || 'ID Pengguna atau Kata Laluan tidak sah.',



          confirmButtonColor: '#1e3a8a'



        });



        return;



      }







      sessionStorage.setItem("koko_session_active", "true");



      state.currentUser = data.user;



      state.activeRole = data.user.role;



      this.updateUserUI();



      



      Swal.fire({



        icon: 'success',



        title: 'Log Masuk Berjaya',



        text: `Selamat datang, ${data.user.full_name}!`,



        timer: 1500,



        showConfirmButton: false



      });







      this.hideLoginView();



      await this.fetchClasses();



      await this.fetchTeachers();



      await this.fetchOrganizations();



      await this.ensureStudentsLoaded();



      



      this.initRouting();



      this.navigate("dashboard", true);



      lucide.createIcons();



    } catch (err) {



      console.error(err);



      Swal.fire({



        icon: 'error',



        title: 'Ralat Sistem',



        text: 'Gagal menghubungi pelayan sistem.',



        confirmButtonColor: '#1e3a8a'



      });



    }



  },







  async fetchActiveUsernamesForLogin() {



    try {



      const select = document.getElementById("login-username-select");



      if (!select) return;



      const res = await fetch("/api/auth/active-users");



      if (res.ok) {



        const users = await res.json();



        const roleIcons = {



          "Admin": "🔴",



          "GPK Kokurikulum": "🟡",



          "Setiausaha Kokurikulum": "🔵",



          "Penyelaras Kokurikulum": "🟣",



          "Guru Penasihat": "🟢"



        };



        



        let html = '<option value="">-- Pilih ID Pengguna Sedia Ada --</option>';



        users.forEach(u => {



          const icon = roleIcons[u.role] || "⚪";



          html += `<option value="${u.username}">${icon} ${u.username} - ${u.full_name} (${u.role})</option>`;



        });



        select.innerHTML = html;



      }



    } catch (e) {



      console.error("Error fetching active usernames:", e);



    }



  },







  onSelectLoginUsername(username) {



    const u = document.getElementById("login-username");



    const p = document.getElementById("login-password");



    if (u) u.value = username || "";



    if (p && username) {



      p.value = "";



      p.focus();



    }



  },







  openPublicRegisterModal() {



    const form = document.getElementById("form-public-register");



    if (form) form.reset();



    this.openModal("modal-public-register");



  },







  async handlePublicRegisterSubmit(e) {



    if (e) e.preventDefault();



    const fullName = document.getElementById("reg-fullname")?.value.trim();



    const username = document.getElementById("reg-username")?.value.trim();



    const password = document.getElementById("reg-password")?.value.trim();



    const phone = document.getElementById("reg-phone")?.value.trim();



    const email = document.getElementById("reg-email")?.value.trim();



    const category = document.getElementById("reg-category")?.value;







    if (!fullName || !username) {



      Swal.fire({



        icon: 'warning',



        title: 'Maklumat Diperlukan',



        text: 'Sila lengkapkan Nama Penuh dan ID Pengguna (Username).'



      });



      return;



    }







    const payload = {



      full_name: fullName,



      username: username,



      password: password || "aba6038",



      phone: phone || null,



      email: email || null,



      assigned_category: category || null



    };







    try {



      const res = await fetch("/api/auth/register", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });



      const data = await res.json();



      if (!res.ok) {



        Swal.fire({



          icon: 'error',



          title: 'Pendaftaran Gagal',



          text: data.detail || 'Ralat berlaku semasa memproses pendaftaran.'



        });



        return;



      }







      this.closeModal("modal-public-register");



      await Swal.fire({



        icon: 'success',



        title: 'Permohonan Dihantar!',



        html: `Permohonan pendaftaran untuk <b>${fullName}</b> (ID: <code>${username}</code>) telah berjaya dihantar ke sistem.<br><br><span class="text-xs text-amber-700 font-bold">ℹ️ Akaun anda kini menunggu pengesahan dan kelulusan daripada Admin atau GPK Kokurikulum sebelum boleh digunakan untuk log masuk.</span>`,



        confirmButtonColor: '#1e3a8a'



      });



    } catch (err) {



      console.error(err);



      Swal.fire({



        icon: 'error',



        title: 'Ralat',



        text: 'Ralat rangkaian semasa menghantar pendaftaran.'



      });



    }



  },







  selectQuickRoleUsername(username) {



    this.onSelectLoginUsername(username);



  },







  quickLoginWithCredentials(username, password) {



    this.onSelectLoginUsername(username);



  },







  openMyProfileModal() {



    if (!state.currentUser) return;



    const roleEl = document.getElementById("my-profile-role");



    const userEl = document.getElementById("my-profile-username");



    const nameEl = document.getElementById("my-profile-fullname");



    const phoneEl = document.getElementById("my-profile-phone");



    const emailEl = document.getElementById("my-profile-email");



    const pwdEl = document.getElementById("my-profile-password");







    if (roleEl) roleEl.value = state.currentUser.role || state.activeRole || "Pengguna";



    if (userEl) userEl.value = state.currentUser.username || "";



    if (nameEl) nameEl.value = state.currentUser.full_name || "";



    if (phoneEl) phoneEl.value = state.currentUser.phone || "";



    if (emailEl) emailEl.value = state.currentUser.email || "";



    if (pwdEl) pwdEl.value = "";







    this.openModal("modal-my-profile");



  },







  async handleSaveMyProfile(e) {



    if (e) e.preventDefault();



    const username = document.getElementById("my-profile-username")?.value.trim();



    const fullName = document.getElementById("my-profile-fullname")?.value.trim();



    const phone = document.getElementById("my-profile-phone")?.value.trim();



    const email = document.getElementById("my-profile-email")?.value.trim();



    const password = document.getElementById("my-profile-password")?.value.trim();







    if (!username || !fullName) {



      Swal.fire({



        icon: 'warning',



        title: 'Maklumat Diperlukan',



        text: 'ID Pengguna (Username) dan Nama Penuh tidak boleh dibiarkan kosong.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }







    const payload = {



      username: username,



      full_name: fullName,



      phone: phone || null,



      email: email || null



    };



    if (password) {



      payload.password = password;



    }







    try {



      const res = await fetch("/api/auth/profile", {



        method: "PUT",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });



      const data = await res.json();



      if (!res.ok) {



        Swal.fire({



          icon: 'error',



          title: 'Gagal Mengemas Kini Profil',



          text: data.detail || 'Ralat berlaku semasa mengemas kini profil.',



          confirmButtonColor: '#1e3a8a'



        });



        return;



      }







      state.currentUser = data.user;



      this.updateUserUI();



      this.closeModal("modal-my-profile");







      Swal.fire({



        icon: 'success',



        title: 'Profil Berjaya Dikemaskini',



        text: data.message || 'ID Pengguna dan profil anda telah berjaya disimpan.',



        timer: 2000,



        showConfirmButton: false



      });



    } catch (err) {



      console.error(err);



      Swal.fire({



        icon: 'error',



        title: 'Ralat',



        text: 'Ralat rangkaian semasa mengemas kini profil.',



        confirmButtonColor: '#1e3a8a'



      });



    }



  },







  togglePasswordVisibility(inputId) {



    const input = document.getElementById(inputId);



    if (!input) return;



    input.type = input.type === "password" ? "text" : "password";



  },







  async logout() {



    const confirm = await Swal.fire({



      title: 'Log Keluar?',



      text: 'Adakah anda pasti untuk log keluar daripada sistem?',



      icon: 'question',



      showCancelButton: true,



      confirmButtonColor: '#e11d48',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Log Keluar',



      cancelButtonText: 'Batal'



    });







    if (confirm.isConfirmed) {



      sessionStorage.removeItem("koko_session_active");



      try {



        await fetch("/api/auth/logout", { method: "POST" });



      } catch (e) {}



      state.currentUser = null;



      window.location.hash = "";



      this.showLoginView();



      



      // Clear password field



      const p = document.getElementById("login-password");



      if (p) p.value = "";







      Swal.fire({



        icon: 'info',



        title: 'Log Keluar Berjaya',



        text: 'Anda telah selamat log keluar dari sistem. Sila log masuk semula pada bila-bila masa.',



        timer: 1800,



        showConfirmButton: false



      });



    }



  },







  async handleRoleSwitch(newRole) {



    try {



      const res = await fetch("/api/auth/switch-role", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ role: newRole })



      });



      if (res.ok) {



        const data = await res.json();



        state.currentUser = data.user;



        state.activeRole = state.currentUser.role;



        this.updateUserUI();



        



        Swal.fire({



          icon: 'success',



          title: 'Peranan Ditukar',



          text: `Anda kini beroperasi sebagai: ${newRole}`,



          toast: true,



          position: 'top-end',



          showConfirmButton: false,



          timer: 2500



        });







        // Refresh active view



        this.navigate(state.currentView, true);



      }



    } catch (err) {



      console.error("Switch role failed:", err);



    }



  },







  async fetchSchoolSettings() {



    try {



      const res = await fetch("/api/settings/school");



      if (res.ok) {



        state.schoolSettings = await res.json();



        const headerSchoolName = document.getElementById("header-school-name");



        if (headerSchoolName) headerSchoolName.textContent = `${state.schoolSettings.school_name} (${state.schoolSettings.school_code})`;



        



        const loginSchoolName = document.getElementById("login-school-name");



        if (loginSchoolName && state.schoolSettings.school_name) loginSchoolName.textContent = state.schoolSettings.school_name;







        const headerSessionYear = document.getElementById("header-session-year");



        if (headerSessionYear) headerSessionYear.textContent = `Sesi ${state.schoolSettings.session_year || '2026/2027'}`;







        if (state.schoolSettings.logo_url) {



          const logoElem = document.getElementById("header-school-logo");



          if (logoElem) logoElem.src = state.schoolSettings.logo_url;



          const loginLogo = document.getElementById("login-school-logo");



          if (loginLogo) loginLogo.src = state.schoolSettings.logo_url;



          const previewElem = document.getElementById("setting-logo-preview");



          if (previewElem) previewElem.src = state.schoolSettings.logo_url;



        }







        // Fill settings form if active



        this.populateSettingsForm();



      }



    } catch (err) {



      console.error("Fetch school settings failed:", err);



    }



  },







  async fetchClasses() {



    try {



      const res = await fetch("/api/settings/classes");



      if (res.ok) {



        state.classes = await res.json();



      }



    } catch (e) {



      console.error(e);



    }



  },







  async fetchTeachers() {



    try {



      const res = await fetch("/api/settings/teachers");



      if (res.ok) {



        state.teachers = await res.json();



      }



    } catch (e) {



      console.error(e);



    }



  },







  async fetchOrganizations() {



    try {



      const res = await fetch("/api/organizations");



      if (res.ok) {



        state.organizations = await res.json();



        this.populateOrgDropdowns();



      }



    } catch (e) {



      console.error(e);



    }



  },







  // ==========================================



  // NAVIGATION & ROUTING



  // ==========================================



  initRouting() {



    if (this._routingInitialized) return;



    this._routingInitialized = true;



    window.addEventListener("hashchange", () => {



      if (!state.currentUser) {



        this.showLoginView();



        return;



      }



      const view = window.location.hash.replace("#", "") || "dashboard";



      this.navigate(view);



    });



  },







  navigate(viewName, force = false) {



    if (!state.currentUser) {



      this.showLoginView();



      return;



    }







    if (viewName === "sports-day") viewName = "sports_day";



    if (viewName === "cross-country") viewName = "cross_country";







    if (state.currentView === viewName && !force) return;



    state.currentView = viewName;







    // Update URL hash



    window.location.hash = viewName.replace("_", "-");







    // Toggle active navigation link



    document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));



    const activeNav = document.getElementById(`nav-${viewName.replace("_", "-")}`) || document.getElementById(`nav-${viewName}`);



    if (activeNav) activeNav.classList.add("active");







    // Hide all views, show requested view



    const views = ["dashboard", "students", "organizations", "attendance", "activities", "permission", "pajsk", "sports-day", "cross-country", "reports", "settings"];



    views.forEach(v => {



      const el = document.getElementById(`view-${v}`);



      if (el) {



        if (v === viewName || v === viewName.replace("_", "-")) {



          el.classList.remove("hidden");



        } else {



          el.classList.add("hidden");



        }



      }



    });







    // Close mobile sidebar if open



    const sidebar = document.getElementById("sidebar");



    const backdrop = document.getElementById("sidebar-backdrop");



    if (sidebar && !sidebar.classList.contains("-translate-x-full")) {



      sidebar.classList.add("-translate-x-full");



      if (backdrop) backdrop.classList.add("hidden");



    }







    // Load data for specific view



    switch (viewName) {



      case "dashboard":



        this.loadDashboard();



        break;



      case "students":



        this.loadStudents();



        break;



      case "organizations":



        this.renderOrganizations();



        break;



      case "attendance":



        this.navigate("activities");



        return;



      case "activities":



        this.loadActivities();



        break;



      case "permission":



        this.loadPermissionLetters();



        break;



      case "pajsk":
        this.populatePajskClassFilter();



        if (state.pajskActiveTab === "students") {



          this.loadStudentPajskAchievements();



        } else {



          this.loadExternalEvents();



        }



        break;



      case "sports_day":



        this.loadSportsDayOverview();



        break;



      case "cross_country":



        this.loadCrossCountryOverview();



        break;



      case "settings":



        this.populateSettingsForm();



        break;



    }







    lucide.createIcons();



  },







  toggleSidebar() {



    const sidebar = document.getElementById("sidebar");



    const backdrop = document.getElementById("sidebar-backdrop");



    if (sidebar) {



      sidebar.classList.toggle("-translate-x-full");



      if (backdrop) backdrop.classList.toggle("hidden");



    }



  },







  // ==========================================



  // VIEW 1: DASHBOARD



  // ==========================================



  async loadDashboard() {



    try {



      const res = await fetch("/api/reports/dashboard-stats");



      if (!res.ok) return;



      const data = await res.json();







      // Metric counters



      document.getElementById("stat-total-students").textContent = data.summary.total_students;



      document.getElementById("stat-house-students").textContent = data.summary.house_count;



      document.getElementById("stat-uniform-students").textContent = data.summary.uniform_count;



      document.getElementById("stat-club-students").textContent = data.summary.club_count;



      document.getElementById("stat-sports-students").textContent = data.summary.sports_count;



      document.getElementById("stat-attendance-rate").textContent = `${data.summary.avg_attendance_rate}%`;



      document.getElementById("stat-external-events").textContent = data.summary.total_external_events;



      document.getElementById("stat-total-achievements").textContent = data.summary.total_achievements;







      // Update badge student count on sidebar



      const badgeCount = document.getElementById("badge-student-count");



      if (badgeCount) badgeCount.textContent = data.summary.total_students;







      // Render Charts



      this.renderCharts(data.charts);







      // Render Upcoming Activities List



      this.renderUpcomingActivities(data.upcoming_activities);



      lucide.createIcons();



    } catch (err) {



      console.error("Dashboard error:", err);



    }



  },







  renderCharts(chartsData) {



    if (!chartsData) return;







    // 1. Level Chart (Doughnut)



    const ctxLevels = document.getElementById("chart-levels");



    if (ctxLevels) {



      if (state.charts.levels) state.charts.levels.destroy();



      state.charts.levels = new Chart(ctxLevels, {



        type: 'doughnut',



        data: {



          labels: ['Zon', 'Daerah', 'Negeri', 'Kebangsaan', 'Antarabangsa'],



          datasets: [{



            data: [



              chartsData.levels.Zon || 0,



              chartsData.levels.Daerah || 0,



              chartsData.levels.Negeri || 0,



              chartsData.levels.Kebangsaan || 0,



              chartsData.levels.Antarabangsa || 0



            ],



            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],



            borderWidth: 2,



            borderColor: '#ffffff'



          }]



        },



        options: {



          responsive: true,



          maintainAspectRatio: false,



          plugins: {



            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 10 } } }



          }



        }



      });



    }







    // 2. Houses Chart (Bar)



    const ctxHouses = document.getElementById("chart-houses");



    if (ctxHouses) {



      if (state.charts.houses) state.charts.houses.destroy();



      const houseLabels = (chartsData.houses || []).map(h => h.name.replace("Rumah ", ""));



      const houseCounts = (chartsData.houses || []).map(h => h.count || 0);



      const houseColors = (chartsData.houses || []).map(h => h.color_code || '#1e3a8a');







      state.charts.houses = new Chart(ctxHouses, {



        type: 'bar',



        data: {



          labels: houseLabels.length ? houseLabels : ['Merah', 'Biru', 'Hijau', 'Kuning'],



          datasets: [{



            label: 'Bil. Murid',



            data: houseCounts.length ? houseCounts : [10, 10, 10, 10],



            backgroundColor: houseColors.length ? houseColors : ['#dc2626', '#2563eb', '#16a34a', '#ca8a04'],



            borderRadius: 6



          }]



        },



        options: {



          responsive: true,



          maintainAspectRatio: false,



          plugins: { legend: { display: false } },



          scales: {



            y: { beginAtZero: true, ticks: { precision: 0 } }



          }



        }



      });



    }



  },







  renderUpcomingActivities(activities) {



    const container = document.getElementById("dashboard-upcoming-list");



    if (!container) return;







    if (!activities || activities.length === 0) {



      container.innerHTML = `



        <div class="text-center py-6 text-slate-400 text-xs">



          <i data-lucide="calendar-off" class="w-8 h-8 mx-auto mb-1 opacity-50"></i>



          Tiada aktiviti dijadualkan dalam masa terdekat



        </div>



      `;



      return;



    }







    container.innerHTML = activities.map(act => `



      <div class="p-2.5 rounded-xl border border-slate-200 bg-white/80 hover:bg-slate-50 transition flex items-center justify-between">



        <div class="flex items-center space-x-3">



          <div class="w-2 h-8 rounded-full" style="background-color: ${act.color_code || '#1e3a8a'}"></div>



          <div>



            <div class="text-xs font-bold text-slate-800 line-clamp-1">${act.title}</div>



            <div class="text-[10px] text-slate-500 flex items-center space-x-2 mt-0.5">



              <span class="font-semibold text-slate-700">${act.org_name}</span>



              <span>•</span>



              <span>${act.activity_date}</span>



            </div>



          </div>



        </div>



        <span class="badge-status text-[10px] ${this.getStatusBadgeClass(act.status)}">



          ${act.status}



        </span>



      </div>



    `).join("");



  },







  getStatusBadgeClass(status) {



    switch (status) {



      case "Disahkan":



      case "Dibenarkan":



      case "Hadir":



      case "Aktif":



        return "bg-emerald-100 text-emerald-800";



      case "Disemak":



      case "Dihantar":



      case "Diterima":



        return "bg-blue-100 text-blue-800";



      case "Draf":



      case "Belum Diedarkan":



        return "bg-slate-100 text-slate-700";



      case "Perlu Pindaan":



      case "Lewat":



        return "bg-amber-100 text-amber-800";



      case "Tidak Hadir":



      case "Tidak Dibenarkan":



        return "bg-rose-100 text-rose-800";



      default:



        return "bg-slate-100 text-slate-700";



    }



  },







  // ==========================================



  // VIEW 2: PENGURUSAN MAKLUMAT MURID



  // ==========================================



  async onStudentCategoryFilterChange() {



    const category = document.getElementById("filter-student-category")?.value || "";



    const orgSelect = document.getElementById("filter-student-org");



    if (!orgSelect) return;







    if (!state.organizations || state.organizations.length === 0) {



      await this.fetchOrganizations();



    }







    if (!category) {



      orgSelect.innerHTML = `<option value="">-- Pilih Kategori Dahulu --</option>`;



      orgSelect.disabled = true;



      orgSelect.className = "w-full py-2 px-3 bg-slate-100 text-slate-400 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-navy-600 outline-none transition";



    } else {



      orgSelect.disabled = false;



      orgSelect.className = "w-full py-2 px-3 bg-white text-slate-800 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-navy-600 outline-none transition";







      let filteredOrgs = [];



      if (state.organizations && Array.isArray(state.organizations)) {



        filteredOrgs = state.organizations.filter(o => o.category === category);



      }







      let categoryLabel = `Semua ${category}`;



      let optionsHtml = "";







      if (category === "Rumah Sukan") {



        categoryLabel = "Semua Rumah Sukan";



        const houseOrder = ["Biru", "Merah", "Hijau", "Kuning"];



        filteredOrgs.sort((a, b) => {



          const aName = a.name.toLowerCase();



          const bName = b.name.toLowerCase();



          const aIdx = houseOrder.findIndex(h => aName.includes(h.toLowerCase()));



          const bIdx = houseOrder.findIndex(h => bName.includes(h.toLowerCase()));



          return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);



        });







        optionsHtml = filteredOrgs.map(o => {



          let displayName = o.name;



          if (o.name.includes("Laksamana") || o.name.includes("Biru")) displayName = "Biru (Rumah Laksamana)";



          else if (o.name.includes("Bendahara") || o.name.includes("Merah")) displayName = "Merah (Rumah Bendahara)";



          else if (o.name.includes("Syahbandar") || o.name.includes("Hijau")) displayName = "Hijau (Rumah Syahbandar)";



          else if (o.name.includes("Temenggong") || o.name.includes("Kuning")) displayName = "Kuning (Rumah Temenggong)";



          return `<option value="${o.id}">${displayName}</option>`;



        }).join("");



      } else if (category === "Unit Beruniform") {



        categoryLabel = "Semua Unit Beruniform";



        filteredOrgs.sort((a, b) => {



          const aName = a.name.toLowerCase();



          const bName = b.name.toLowerCase();



          const aPriority = aName.includes("pengakap") ? 1 : (aName.includes("kadet") || aName.includes("tkrs") ? 2 : 3);



          const bPriority = bName.includes("pengakap") ? 1 : (bName.includes("kadet") || bName.includes("tkrs") ? 2 : 3);



          return aPriority - bPriority;



        });







        optionsHtml = filteredOrgs.map(o => {



          let displayName = o.name;



          if (o.name.toLowerCase().includes("pengakap")) displayName = "Pengakap (Persekutuan Pengakap Malaysia)";



          else if (o.name.toLowerCase().includes("tkrs") || o.name.toLowerCase().includes("tunas kadet")) displayName = "Tunas Kadet Remaja Sekolah (TKRS)";



          return `<option value="${o.id}">${displayName}</option>`;



        }).join("");



      } else if (category === "Kelab & Persatuan") {



        categoryLabel = "Semua Kelab & Persatuan";



        optionsHtml = filteredOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join("");



      } else if (category === "Sukan & Permainan") {



        categoryLabel = "Semua Sukan & Permainan";



        optionsHtml = filteredOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join("");



      }







      orgSelect.innerHTML = `<option value="">${categoryLabel}</option>` + optionsHtml;



    }







    this.filterStudents();



  },







  async loadStudents() {



    try {



      const search = document.getElementById("filter-student-search")?.value || "";



      const grade = document.getElementById("filter-student-grade")?.value || "";



      const gender = document.getElementById("filter-student-gender")?.value || "";



      const category = document.getElementById("filter-student-category")?.value || "";



      const orgId = document.getElementById("filter-student-org")?.value || "";







      let url = `/api/students?limit=500`;



      if (search) url += `&search=${encodeURIComponent(search)}`;



      if (grade) url += `&grade=${grade}`;



      if (gender) url += `&gender=${encodeURIComponent(gender)}`;







      if (category) {



        if (orgId) {



          if (category === "Rumah Sukan") url += `&sport_house_id=${orgId}`;



          else if (category === "Unit Beruniform") url += `&uniform_unit_id=${orgId}`;



          else if (category === "Kelab & Persatuan") url += `&club_society_id=${orgId}`;



          else if (category === "Sukan & Permainan") url += `&sports_game_id=${orgId}`;



        } else {



          url += `&category=${encodeURIComponent(category)}`;



        }



      }







      const res = await fetch(url);



      if (!res.ok) return;



      state.students = await res.json();







      this.renderStudentsTable();







      // If unfiltered, update badge on sidebar directly



      if (!search && !grade && !gender && !category && !orgId) {



        const badgeCount = document.getElementById("badge-student-count");



        if (badgeCount) badgeCount.textContent = state.students.length;



      }



    } catch (err) {



      console.error("Load students error:", err);



    }



  },







  filterStudents() {



    this.loadStudents();



  },







  renderStudentsTable() {



    const tbody = document.getElementById("student-table-body");



    const countElem = document.getElementById("students-shown-count");



    if (!tbody) return;







    countElem.textContent = state.students.length;







    if (state.students.length === 0) {



      tbody.innerHTML = `



        <tr>



          <td colspan="7" class="p-8 text-center text-slate-400">



            <i data-lucide="user-x" class="w-8 h-8 mx-auto mb-1 opacity-50"></i>



            Tiada rekod murid ditemui



          </td>



        </tr>



      `;



      lucide.createIcons();



      return;



    }







    tbody.innerHTML = state.students.map((s, idx) => {



      const isChecked = state.selectedStudentIds.has(s.id);



      return `



        <tr class="hover:bg-slate-50 transition ${isChecked ? 'bg-blue-50/50' : ''}">



          <td class="p-3.5 text-center">



            <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="app.toggleStudentSelection(${s.id}, this.checked)" class="rounded border-slate-300 text-navy-800 focus:ring-navy-600 cursor-pointer">



          </td>



          <td class="p-3.5">



            <div class="font-bold text-slate-900">${s.full_name}</div>



            <div class="text-[11px] text-slate-500 font-mono">${s.ic_number} • <span class="${s.gender === 'Lelaki' ? 'text-blue-600' : 'text-pink-600'} font-semibold">${s.gender}</span></div>



          </td>



          <td class="p-3.5">



            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-700">



              ${s.class_name}



            </span>



          </td>



          <td class="p-3.5">



            ${s.sport_house_name ? `



              <span class="inline-flex items-center text-xs font-semibold" style="color: ${s.sport_house_color || '#dc2626'}">



                <span class="w-2 h-2 rounded-full mr-1.5" style="background-color: ${s.sport_house_color || '#dc2626'}"></span>



                ${s.sport_house_name}



              </span>



            ` : '<span class="text-slate-400 italic text-[11px]">-</span>'}



          </td>



          <td class="p-3.5">



            ${s.uniform_unit_name ? `



              <span class="text-xs font-semibold text-cyan-900">${s.uniform_unit_name}</span>



            ` : '<span class="text-slate-400 italic text-[11px]">-</span>'}



          </td>



          <td class="p-3.5">



            <div class="text-[11px] text-amber-900 font-medium">${s.club_society_name || '-'}</div>



            <div class="text-[11px] text-emerald-900 font-medium">${s.sports_game_name || '-'}</div>



          </td>



          <td class="p-3.5 text-center">



            <div class="flex items-center justify-center space-x-1.5">



              <button onclick="app.openStudentProfile(${s.id})" title="Profil Lengkap" class="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg transition">



                <i data-lucide="eye" class="w-4 h-4"></i>



              </button>



              <button onclick="app.openStudentModal(${s.id})" title="Edit Murid" class="p-1.5 text-slate-600 hover:bg-slate-200 rounded-lg transition">



                <i data-lucide="edit-2" class="w-4 h-4"></i>



              </button>



              ${this.canDelete() ? `



              <button onclick="app.deleteStudent(${s.id})" title="Padam Murid" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg transition">



                <i data-lucide="trash-2" class="w-4 h-4"></i>



              </button>



              ` : ''}



            </div>



          </td>



        </tr>



      `;



    }).join("");







    lucide.createIcons();



    this.updateBulkToolbar();



  },







  toggleStudentSelection(studentId, isChecked) {



    if (isChecked) {



      state.selectedStudentIds.add(studentId);



    } else {



      state.selectedStudentIds.delete(studentId);



    }



    this.updateBulkToolbar();



  },







  toggleSelectAllStudents(isChecked) {



    if (isChecked) {



      state.students.forEach(s => state.selectedStudentIds.add(s.id));



    } else {



      state.selectedStudentIds.clear();



    }



    this.renderStudentsTable();



  },







  clearStudentSelection() {



    state.selectedStudentIds.clear();



    const checkAll = document.getElementById("check-all-students");



    if (checkAll) checkAll.checked = false;



    this.renderStudentsTable();



  },







  updateBulkToolbar() {



    const toolbar = document.getElementById("student-bulk-toolbar");



    const countElem = document.getElementById("selected-students-count");



    if (!toolbar) return;







    const count = state.selectedStudentIds.size;



    if (count > 0) {



      toolbar.classList.remove("hidden");



      countElem.textContent = count;



    } else {



      toolbar.classList.add("hidden");



    }



  },







  openStudentModal(studentId = null) {

    const modal = document.getElementById("modal-student");

    const title = document.getElementById("modal-student-title");

    const form = document.getElementById("form-student");

    if (form) form.reset();

    document.getElementById("student-form-id").value = "";



    // Populate Org Selects

    this.populateStudentModalOrgs();



    if (studentId) {

      title.textContent = "Kemaskini Maklumat Murid";

      const s = state.students.find(x => x.id === studentId);

      if (s) {

        document.getElementById("student-form-id").value = s.id;

        document.getElementById("student-name").value = s.full_name || "";

        document.getElementById("student-ic").value = s.ic_number || "";

        document.getElementById("student-gender").value = s.gender || "Lelaki";

        document.getElementById("student-grade").value = s.grade || 1;

        this.updateClassDropdown(s.grade || 1);



        // Ensure fixed class or existing class is properly selected

        const fixedMap = { 1: '1 UM', 2: '2 UKM', 3: '3 UPM', 4: '4 USM', 5: '5 UTM', 6: '6 UITM' };

        const targetClass = s.class_name || fixedMap[s.grade || 1] || '1 UM';

        const classSelect = document.getElementById("student-class");

        if (classSelect) {

          const exists = Array.from(classSelect.options).some(o => o.value === targetClass);

          if (!exists) {

            const opt = document.createElement("option");

            opt.value = targetClass;

            opt.textContent = targetClass;

            classSelect.appendChild(opt);

          }

          classSelect.value = targetClass;

        }



        document.getElementById("student-guardian").value = s.guardian_name || "";

        document.getElementById("student-guardian-phone").value = s.guardian_phone || "";

        document.getElementById("student-address").value = s.address || "";

        document.getElementById("student-health").value = s.health_info || "";



        document.getElementById("student-house-select").value = s.sport_house_id || "";

        document.getElementById("student-uniform-select").value = s.uniform_unit_id || "";

        document.getElementById("student-club-select").value = s.club_society_id || "";

        document.getElementById("student-sports-select").value = s.sports_game_id || "";

      }

    } else {

      title.textContent = "Daftar Murid Baharu";

      this.updateClassDropdown(1);

    }



    modal.classList.remove("hidden");

    lucide.createIcons();

  },



  updateClassDropdown(grade) {

    const classSelect = document.getElementById("student-class");

    if (!classSelect) return;

    const g = parseInt(grade) || 1;

    const fixedClassesMap = {

      1: ['1 UM'],

      2: ['2 UKM'],

      3: ['3 UPM'],

      4: ['4 USM'],

      5: ['5 UTM'],

      6: ['6 UITM']

    };

    const defaultList = fixedClassesMap[g] || [`${g} UM`];

    const dbList = (state.classes || [])

      .filter(c => c.grade === g)

      .map(c => c.class_name);

    const combined = Array.from(new Set([...defaultList, ...dbList]));

    classSelect.innerHTML = combined.map(c => `<option value="${c}">${c}</option>`).join("");

    if (combined.length > 0) {

      classSelect.value = combined[0];

    }

  },



  populateStudentModalOrgs() {

    const houses = state.organizations.filter(o => o.category === "Rumah Sukan");

    const uniforms = state.organizations.filter(o => o.category === "Unit Beruniform");

    const clubs = state.organizations.filter(o => o.category === "Kelab & Persatuan" || o.category === "Kelab dan Persatuan");

    const sports = state.organizations.filter(o => o.category === "Sukan & Permainan" || o.category === "Sukan dan Permainan");



    document.getElementById("student-house-select").innerHTML = `<option value="">-- Belum Ditetapkan --</option>` + houses.map(o => `<option value="${o.id}">${o.name}</option>`).join("");

    document.getElementById("student-uniform-select").innerHTML = `<option value="">-- Belum Ditetapkan --</option>` + uniforms.map(o => `<option value="${o.id}">${o.name}</option>`).join("");

    document.getElementById("student-club-select").innerHTML = `<option value="">-- Belum Ditetapkan --</option>` + clubs.map(o => `<option value="${o.id}">${o.name}</option>`).join("");

    document.getElementById("student-sports-select").innerHTML = `<option value="">-- Belum Ditetapkan --</option>` + sports.map(o => `<option value="${o.id}">${o.name}</option>`).join("");

  },



  async saveStudent(e) {

    if (e) e.preventDefault();

    const id = document.getElementById("student-form-id").value;



    const rawName = (document.getElementById("student-name").value || "").trim();

    const rawIc = (document.getElementById("student-ic").value || "").trim();

    const rawGrade = parseInt(document.getElementById("student-grade").value) || 1;

    const fixedClassesMap = {

      1: '1 UM',

      2: '2 UKM',

      3: '3 UPM',

      4: '4 USM',

      5: '5 UTM',

      6: '6 UITM'

    };

    const rawClass = (document.getElementById("student-class").value || "").trim() || fixedClassesMap[rawGrade] || `${rawGrade} UM`;

    const rawGender = document.getElementById("student-gender").value || "Lelaki";



    // Allows saving even if incomplete / partial info

    const payload = {

      full_name: rawName ? rawName.toUpperCase() : 'MURID TANPA NAMA',

      ic_number: rawIc || null,

      gender: rawGender,

      grade: rawGrade,

      class_name: rawClass,

      guardian_name: document.getElementById("student-guardian").value.trim() || null,

      guardian_phone: document.getElementById("student-guardian-phone").value.trim() || null,

      address: document.getElementById("student-address").value.trim() || null,

      health_info: document.getElementById("student-health").value.trim() || "Tiada",

      sport_house_id: parseInt(document.getElementById("student-house-select").value) || null,

      uniform_unit_id: parseInt(document.getElementById("student-uniform-select").value) || null,

      club_society_id: parseInt(document.getElementById("student-club-select").value) || null,

      sports_game_id: parseInt(document.getElementById("student-sports-select").value) || null,

      status: "Aktif"

    };



    try {

      let res;

      if (id) {

        res = await fetch(`/api/students/${id}`, {

          method: "PUT",

          headers: { "Content-Type": "application/json" },

          body: JSON.stringify(payload)

        });

      } else {

        res = await fetch("/api/students", {

          method: "POST",

          headers: { "Content-Type": "application/json" },

          body: JSON.stringify(payload)

        });

      }



      if (res.ok) {

        this.closeModal("modal-student");

        Swal.fire({

          icon: 'success',

          title: 'Berjaya',

          text: id ? 'Maklumat murid berjaya dikemas kini!' : 'Murid baharu berjaya didaftarkan!',

          timer: 2000,

          showConfirmButton: false

        });

        await this.loadStudents();

        await this.fetchOrganizations();

      } else {

        const data = await res.json().catch(() => ({}));

        Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal menyimpan rekod murid.' });

      }

    } catch (err) {

      console.error(err);

      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat sambungan pelayan.' });

    }

  },

  async deleteStudent(studentId, name = null) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk memadam maklumat murid. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    if (!name) {



      const s = state.students?.find(x => x.id === studentId);



      name = s ? s.full_name : 'murid ini';



    }



    const result = await Swal.fire({



      title: 'Adakah anda pasti?',



      text: `Padam murid ${name}? Semua rekod kehadiran dan penglibatan murid ini akan dikeluarkan.`,



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#dc2626',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Padam!',



      cancelButtonText: 'Batal'



    });







    if (result.isConfirmed) {



      try {



        const res = await fetch(`/api/students/${studentId}`, { method: "DELETE" });



        if (res.ok) {



          Swal.fire({ icon: 'success', title: 'Dipadam', text: 'Murid berjaya dipadam.', timer: 1500, showConfirmButton: false });



          await this.loadStudents();



        } else {



          Swal.fire({ icon: 'error', title: 'Ralat', text: 'Gagal memadam murid.' });



        }



      } catch (err) {



        console.error(err);



      }



    }



  },







  openImportModal() {



    document.getElementById("input-import-file").value = "";



    document.getElementById("modal-import").classList.remove("hidden");



    lucide.createIcons();



  },







  async handleStudentImport() {



    const fileInput = document.getElementById("input-import-file");



    if (!fileInput.files || fileInput.files.length === 0) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih fail Excel (.xlsx) atau CSV untuk diimport.' });



      return;



    }







    const formData = new FormData();



    formData.append("file", fileInput.files[0]);







    try {



      Swal.fire({



        title: 'Sedang Mengimport...',



        text: 'Memproses fail dan mengemas kini pangkalan data...',



        allowOutsideClick: false,



        didOpen: () => { Swal.showLoading(); }



      });







      const res = await fetch("/api/students/import", {



        method: "POST",



        body: formData



      });







      const data = await res.json();



      if (res.ok) {



        this.closeModal("modal-import");



        const imported = data.imported_count || 0;



        const updated = data.updated_count || 0;



        const total = imported + updated;



        const errors = data.errors || [];







        if (total > 0) {



          let htmlContent = `



            <div class="text-left text-xs space-y-3">



              <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800">



                <p class="font-bold text-sm text-emerald-900 mb-1">Ringkasan Pemprosesan:</p>



                <div class="space-y-1">



                  <div>• Murid baharu didaftarkan: <b class="text-emerald-950 font-bold">${imported}</b> orang</div>



                  <div>• Rekod murid dikemas kini: <b class="text-emerald-950 font-bold">${updated}</b> orang</div>



                  <div>• Jumlah keseluruhan diproses: <b class="text-emerald-950 font-bold">${total}</b> orang</div>



                </div>



              </div>



          `;



          if (errors.length > 0) {



            htmlContent += `



              <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800">



                <p class="font-bold text-amber-900 mb-1">Perhatian (${errors.length} baris tidak dapat diproses):</p>



                <div class="max-h-32 overflow-y-auto mt-1 space-y-1 font-mono text-[11px] text-amber-950">



                  ${errors.map(e => `<div>• ${e}</div>`).join('')}



                </div>



              </div>



            `;



          }



          htmlContent += `</div>`;







          Swal.fire({



            icon: 'success',



            title: 'Import Berjaya',



            html: htmlContent,



            confirmButtonColor: '#059669',



            confirmButtonText: 'Selesai'



          });



        } else {



          let htmlContent = `



            <div class="text-left text-xs space-y-3">



              <div class="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">



                <p class="font-bold text-sm text-rose-900 mb-1">Tiada Data Dimasukkan</p>



                <p class="leading-relaxed">Tiada murid baharu didaftarkan atau dikemas kini daripada fail yang dimuat naik. Sila pastikan fail anda mengandungi ruangan <b>Nama Murid</b> dan <b>No KP / MyKid</b>.</p>



              </div>



          `;



          if (errors.length > 0) {



            htmlContent += `



              <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-slate-700">



                <p class="font-bold text-slate-800 mb-1">Perincian Ralat (${errors.length} baris):</p>



                <div class="max-h-36 overflow-y-auto mt-1 space-y-1 font-mono text-[11px] text-rose-600">



                  ${errors.map(e => `<div>• ${e}</div>`).join('')}



                </div>



              </div>



            `;



          }



          htmlContent += `</div>`;







          Swal.fire({



            icon: 'warning',



            title: 'Import Tidak Berjaya',



            html: htmlContent,



            confirmButtonColor: '#d97706',



            confirmButtonText: 'Faham'



          });



        }







        // Reset filter inputs so all newly imported students are visible immediately



        const searchInput = document.getElementById("filter-student-search");



        if (searchInput) searchInput.value = "";



        const gradeInput = document.getElementById("filter-student-grade");



        if (gradeInput) gradeInput.value = "";



        const genderInput = document.getElementById("filter-student-gender");



        if (genderInput) genderInput.value = "";



        const catInput = document.getElementById("filter-student-category");



        if (catInput) catInput.value = "";



        const orgInput = document.getElementById("filter-student-org");



        if (orgInput) orgInput.value = "";







        await this.loadStudents();



        await this.loadDashboard();



      } else {



        Swal.fire({ icon: 'error', title: 'Ralat Import', text: data.detail || 'Gagal memproses fail.' });



      }



    } catch (err) {



      console.error(err);



      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memuat naik fail: ' + (err.message || err) });



    }



  },







  exportStudentsExcel() {



    if (state.selectedStudentIds && state.selectedStudentIds.size > 0) {



      const ids = Array.from(state.selectedStudentIds).join(",");



      window.location.href = `/api/students/export/excel?ids=${ids}`;



      return;



    }







    const search = document.getElementById("filter-student-search")?.value?.trim() || "";



    const grade = document.getElementById("filter-student-grade")?.value || "";



    const gender = document.getElementById("filter-student-gender")?.value || "";



    const category = document.getElementById("filter-student-category")?.value || "";



    const orgId = document.getElementById("filter-student-org")?.value || "";







    const params = [];



    if (search) params.push(`search=${encodeURIComponent(search)}`);



    if (grade) params.push(`grade=${grade}`);



    if (gender) params.push(`gender=${encodeURIComponent(gender)}`);



    if (category) {



      if (orgId) {



        if (category === "Rumah Sukan") params.push(`sport_house_id=${orgId}`);



        else if (category === "Unit Beruniform") params.push(`uniform_unit_id=${orgId}`);



        else if (category === "Kelab & Persatuan") params.push(`club_society_id=${orgId}`);



        else if (category === "Sukan & Permainan") params.push(`sports_game_id=${orgId}`);



      } else {



        params.push(`category=${encodeURIComponent(category)}`);



      }



    }







    const q = params.length > 0 ? `?${params.join("&")}` : "";



    window.location.href = `/api/students/export/excel${q}`;



  },







  printCurrentStudentList() {



    if (state.selectedStudentIds && state.selectedStudentIds.size > 0) {



      this.printSelectedStudents();



      return;



    }







    const search = document.getElementById("filter-student-search")?.value?.trim() || "";



    const grade = document.getElementById("filter-student-grade")?.value || "";



    const gender = document.getElementById("filter-student-gender")?.value || "";



    const category = document.getElementById("filter-student-category")?.value || "";



    const orgId = document.getElementById("filter-student-org")?.value || "";







    const params = {};



    if (search) params.search = search;



    if (grade) params.grade = grade;



    if (gender) params.gender = gender;



    if (category) {



      if (orgId) {



        if (category === "Rumah Sukan") params.sport_house_id = orgId;



        else if (category === "Unit Beruniform") params.uniform_unit_id = orgId;



        else if (category === "Kelab & Persatuan") params.club_society_id = orgId;



        else if (category === "Sukan & Permainan") params.sports_game_id = orgId;



      } else {



        params.category = category;



      }



    }







    this.prepareReport("filtered_students", params);



  },







  printSelectedStudents() {



    if (!state.selectedStudentIds || state.selectedStudentIds.size === 0) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila tanda kotak sekurang-kurangnya seorang murid.' });



      return;



    }



    const ids = Array.from(state.selectedStudentIds).join(",");



    this.prepareReport("filtered_students", { ids: ids });



  },







  // ==========================================



  // VIEW 2.1: STUDENT FULL PROFILE MODAL



  // ==========================================



  async openStudentProfile(studentId) {



    try {



      const res = await fetch(`/api/students/${studentId}`);



      if (!res.ok) return;



      const s = await res.json();







      document.getElementById("profile-avatar").textContent = s.full_name.substring(0, 2).toUpperCase();



      document.getElementById("profile-full-name").textContent = s.full_name;



      document.getElementById("profile-sub-meta").textContent = `${s.class_name} • No KP: ${s.ic_number} • ${s.gender}`;







      const content = document.getElementById("student-profile-content");



      content.innerHTML = `



        <!-- Bio & PAJSK Score Card Summary -->



        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">



          <!-- PAJSK Big Gauge -->



          <div class="p-4 rounded-2xl bg-gradient-to-br from-navy-900 to-blue-900 text-white flex flex-col justify-between">



            <div>



              <span class="text-[10px] font-bold uppercase tracking-wider text-blue-200">Skor Anggaran PAJSK</span>



              <div class="text-3xl font-black mt-1">${s.pajsk_summary.total_score} <span class="text-xs font-normal text-blue-300">/ 100</span></div>



              <div class="inline-block px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500 text-white mt-1">Gred ${s.pajsk_summary.grade}</div>



            </div>



            <div class="space-y-1 text-[11px] text-blue-100 pt-3 border-t border-blue-800">



              <div class="flex justify-between"><span>Kehadiran:</span> <span class="font-bold">${s.pajsk_summary.attendance_score}m</span></div>



              <div class="flex justify-between"><span>Jawatan AJK:</span> <span class="font-bold">${s.pajsk_summary.position_score}m</span></div>



              <div class="flex justify-between"><span>Penglibatan & Sukan:</span> <span class="font-bold">${s.pajsk_summary.participation_score}m</span></div>



              <div class="flex justify-between"><span>Ekstra Kurikulum:</span> <span class="font-bold">${s.pajsk_summary.extra_curriculum_score}m</span></div>



            </div>



          </div>







          <!-- 4 Organizations Assigned -->



          <div class="md:col-span-2 p-4 rounded-2xl bg-slate-50 border border-slate-200 grid grid-cols-2 gap-3">



            <div class="p-2.5 bg-white rounded-xl border border-slate-200">



              <span class="text-[10px] font-bold text-slate-400 uppercase">Rumah Sukan</span>



              <div class="text-xs font-bold text-slate-800 mt-0.5">${s.sport_house_name || '-'}</div>



            </div>



            <div class="p-2.5 bg-white rounded-xl border border-slate-200">



              <span class="text-[10px] font-bold text-slate-400 uppercase">Unit Beruniform</span>



              <div class="text-xs font-bold text-slate-800 mt-0.5">${s.uniform_unit_name || '-'}</div>



            </div>



            <div class="p-2.5 bg-white rounded-xl border border-slate-200">



              <span class="text-[10px] font-bold text-slate-400 uppercase">Kelab & Persatuan</span>



              <div class="text-xs font-bold text-slate-800 mt-0.5">${s.club_society_name || '-'}</div>



            </div>



            <div class="p-2.5 bg-white rounded-xl border border-slate-200">



              <span class="text-[10px] font-bold text-slate-400 uppercase">Sukan & Permainan</span>



              <div class="text-xs font-bold text-slate-800 mt-0.5">${s.sports_game_name || '-'}</div>



            </div>



            <div class="col-span-2 text-[11px] text-slate-500 pt-1">



              <span class="font-bold text-slate-700">Penjaga:</span> ${s.guardian_name || '-'} (${s.guardian_phone || '-'}) • <span class="font-bold text-slate-700">Kesihatan:</span> ${s.health_info || 'Tiada rekod alahan'}



            </div>



          </div>



        </div>







        <!-- Jawatankuasa / Committees Held -->



        <div>



          <h4 class="font-bold text-navy-900 mb-2 uppercase text-xs">Jawatan Jawatankuasa Murid (AJK)</h4>



          <div class="border border-slate-200 rounded-xl overflow-hidden">



            <table class="w-full text-left text-xs">



              <thead class="bg-slate-100 font-bold">



                <tr>



                  <th class="p-2.5">Organisasi</th>



                  <th class="p-2.5">Kategori</th>



                  <th class="p-2.5">Jawatan Disandang</th>



                </tr>



              </thead>



              <tbody class="divide-y divide-slate-200">



                ${s.committees.length > 0 ? s.committees.map(c => `



                  <tr>



                    <td class="p-2.5 font-bold">${c.org_name}</td>



                    <td class="p-2.5 text-slate-600">${c.org_category}</td>



                    <td class="p-2.5"><span class="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-md font-bold text-[11px]">${c.position}</span></td>



                  </tr>



                `).join("") : '<tr><td colspan="3" class="p-3 text-center text-slate-400">Tiada jawatan khas disandang (Ahli Biasa)</td></tr>'}



              </tbody>



            </table>



          </div>



        </div>







        <!-- External Participations & PAJSK Records -->



        <div>



          <h4 class="font-bold text-navy-900 mb-2 uppercase text-xs">Penyertaan Pertandingan & Aktiviti Luar Sekolah</h4>



          <div class="border border-slate-200 rounded-xl overflow-hidden">



            <table class="w-full text-left text-xs">



              <thead class="bg-slate-100 font-bold">



                <tr>



                  <th class="p-2.5">Tarikh</th>



                  <th class="p-2.5">Nama Program</th>



                  <th class="p-2.5">Peringkat</th>



                  <th class="p-2.5">Pencapaian</th>



                  <th class="p-2.5 text-center">Skor PAJSK</th>



                </tr>



              </thead>



              <tbody class="divide-y divide-slate-200">



                ${s.external_participations.length > 0 ? s.external_participations.map(ep => `



                  <tr>



                    <td class="p-2.5">${ep.event_date}</td>



                    <td class="p-2.5 font-bold">${ep.program_name}</td>



                    <td class="p-2.5"><span class="px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-semibold text-[11px]">${ep.participation_level}</span></td>



                    <td class="p-2.5 font-semibold text-emerald-800">${ep.achievement}</td>



                    <td class="p-2.5 text-center font-bold text-navy-900">${ep.pajsk_score}m</td>



                  </tr>



                `).join("") : '<tr><td colspan="5" class="p-3 text-center text-slate-400">Tiada rekod penyertaan luar didaftarkan</td></tr>'}



              </tbody>



            </table>



          </div>



        </div>



      `;







      state.currentViewingStudent = s;



      document.getElementById("modal-student-profile").classList.remove("hidden");



      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  printSingleStudentProfile() {



    if (!state.currentViewingStudent) return;



    this.prepareReport("individual_student_profile", { student_id: state.currentViewingStudent.id });



  },







  // ==========================================



  // VIEW 2.2: BULK ASSIGN ORG



  // ==========================================



  openBulkAssignModal() {



    if (state.selectedStudentIds.size === 0) return;



    this.updateBulkOrgDropdown("Rumah Sukan");



    document.getElementById("modal-bulk-assign").classList.remove("hidden");



    lucide.createIcons();



  },







  updateBulkOrgDropdown(category) {



    const orgSelect = document.getElementById("bulk-org-select");



    const filtered = state.organizations.filter(o => o.category === category);



    orgSelect.innerHTML = filtered.map(o => `<option value="${o.id}">${o.name}</option>`).join("");



  },







  async executeBulkAssign() {



    const category = document.getElementById("bulk-category-select").value;



    const orgId = parseInt(document.getElementById("bulk-org-select").value);



    const studentIds = Array.from(state.selectedStudentIds);







    try {



      const res = await fetch("/api/students/bulk-assign", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({



          student_ids: studentIds,



          category: category,



          organization_id: orgId



        })



      });







      if (res.ok) {



        this.closeModal("modal-bulk-assign");



        this.clearStudentSelection();



        Swal.fire({



          icon: 'success',



          title: 'Berjaya',



          text: `Organisasi telah berjaya ditetapkan kepada ${studentIds.length} murid!`,



          timer: 2000,



          showConfirmButton: false



        });



        await this.loadStudents();



        await this.loadDashboard();



      }



    } catch (err) {



      console.error(err);



    }



  },







  // ==========================================



  // VIEW 3: ORGANISASI KOKURIKULUM



  // ==========================================



  populateOrgDropdowns() {



    // Filter selectors



    const attOrgSelect = document.getElementById("filter-att-org");



    const actOrgSelect = document.getElementById("filter-act-org");



    const attFormOrg = document.getElementById("att-form-org");



    const actFormOrg = document.getElementById("act-form-org");



    const pajskFormOrg = document.getElementById("pajsk-form-org");







    // Sync cascading student category filter



    if (document.getElementById("filter-student-category")) {



      this.onStudentCategoryFilterChange();



    }







    const allOrgsOptions = `<option value="">Semua Organisasi</option>` + state.organizations.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("");



    if (attOrgSelect) attOrgSelect.innerHTML = allOrgsOptions;



    if (actOrgSelect) actOrgSelect.innerHTML = allOrgsOptions;







    const orgsOnly = state.organizations.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("");



    if (attFormOrg) attFormOrg.innerHTML = orgsOnly;



    if (actFormOrg) actFormOrg.innerHTML = orgsOnly;



    if (pajskFormOrg) pajskFormOrg.innerHTML = `<option value="">-- Tiada / Wakil Terbuka --</option>` + orgsOnly;



  },







  switchOrgTab(category) {



    state.currentOrgTab = category;



    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));



    



    if (category === "all") document.getElementById("tab-org-all")?.classList.add("active");



    else if (category === "Rumah Sukan") document.getElementById("tab-org-house")?.classList.add("active");



    else if (category === "Unit Beruniform") document.getElementById("tab-org-uniform")?.classList.add("active");



    else if (category === "Kelab & Persatuan") document.getElementById("tab-org-club")?.classList.add("active");



    else if (category === "Sukan & Permainan") document.getElementById("tab-org-sports")?.classList.add("active");







    this.renderOrganizations();



  },







  renderOrganizations() {



    const container = document.getElementById("org-cards-container");



    if (!container) return;







    let filtered = state.organizations;



    if (state.currentOrgTab !== "all") {



      filtered = filtered.filter(o => o.category === state.currentOrgTab);



    }







    if (filtered.length === 0) {



      container.innerHTML = `



        <div class="col-span-3 text-center py-12 text-slate-400">



          <i data-lucide="layers" class="w-10 h-10 mx-auto mb-2 opacity-50"></i>



          Tiada organisasi didaftarkan bagi kategori ini



        </div>



      `;



      lucide.createIcons();



      return;



    }







    container.innerHTML = filtered.map(o => `



      <div class="stat-card glass-card p-5 rounded-2xl flex flex-col justify-between border-t-4" style="border-top-color: ${o.color_code || '#1e3a8a'}">



        <div>



          <div class="flex items-center justify-between">



            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">${o.category}</span>



            <span class="text-xs font-bold text-navy-900 flex items-center">



              <i data-lucide="users" class="w-3.5 h-3.5 mr-1 text-slate-500"></i>



              ${o.member_count || 0} Ahli



            </span>



          </div>



          <h3 class="text-sm font-bold text-slate-900 mt-2">${o.name}</h3>



          <p class="text-[11px] text-slate-500 mt-1 line-clamp-2">${o.vision_mission || 'Membina sahsiah, disiplin dan kemahiran murid SK Sungai Dendang.'}</p>



          



          <div class="mt-3 pt-3 border-t border-slate-100 space-y-1 text-[11px] text-slate-600">



            <div><span class="font-semibold text-slate-800">Guru Penasihat:</span> ${o.advisor_teachers || '-'}</div>



            <div><span class="font-semibold text-slate-800">Hari & Waktu:</span> ${o.meeting_day || 'Rabu'} (${o.meeting_time || '2:00 - 4:00 Petang'})</div>



            <div><span class="font-semibold text-slate-800">Tempat:</span> ${o.meeting_venue || 'Sekolah'}</div>



          </div>



        </div>







        <div class="pt-4 mt-3 border-t border-slate-100 flex items-center justify-between">



          <button onclick="app.openOrgManageModal(${o.id})" class="px-3 py-1.5 bg-navy-800 hover:bg-navy-900 text-white rounded-xl text-xs font-semibold flex items-center space-x-1 transition shadow-sm">



            <i data-lucide="users-round" class="w-3.5 h-3.5"></i>



            <span>Urus Ahli & AJK</span>



          </button>



          <div class="flex items-center space-x-1">



            <button onclick="app.openOrgModal(${o.id})" title="Kemaskini Butiran Organisasi" class="p-1.5 text-slate-700 hover:bg-slate-200 rounded-lg transition">



              <i data-lucide="edit-3" class="w-4 h-4"></i>



            </button>



            <button onclick="app.prepareReport('org_chart', { org_id: ${o.id} })" title="Pratonton Carta Organisasi" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg">



              <i data-lucide="printer" class="w-4 h-4"></i>



            </button>



            ${this.canDelete() ? `



            <button onclick="app.deleteOrg(${o.id})" title="Padam" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg">



              <i data-lucide="trash-2" class="w-4 h-4"></i>



            </button>



            ` : ''}



          </div>



        </div>



      </div>



    `).join("");







    lucide.createIcons();



  },







  openOrgModal(orgId = null) {



    let modal = document.getElementById("modal-org");



    if (!modal) {



      this.injectOrgModalDOM();



      modal = document.getElementById("modal-org");



    }



    if (!modal) {



      console.error("modal-org could not be initialized");



      return;



    }







    const form = document.getElementById("form-org");



    if (form) form.reset();



    const idElem = document.getElementById("org-form-id");



    if (idElem) idElem.value = "";







    if (orgId && state.organizations) {



      const org = state.organizations.find(o => o.id === orgId);



      if (org) {



        const titleElem = document.getElementById("modal-org-title");



        if (titleElem) titleElem.textContent = `Kemaskini Organisasi: ${org.name}`;



        if (idElem) idElem.value = org.id;



        if (document.getElementById("org-form-name")) document.getElementById("org-form-name").value = org.name || "";



        if (document.getElementById("org-form-category")) document.getElementById("org-form-category").value = org.category || "Kelab & Persatuan";



        if (document.getElementById("org-form-color")) document.getElementById("org-form-color").value = org.color_code || "#1e3a8a";



        if (document.getElementById("org-form-color-text")) document.getElementById("org-form-color-text").value = org.color_code || "#1e3a8a";



        if (document.getElementById("org-form-advisors")) document.getElementById("org-form-advisors").value = org.advisor_teachers || "";



        if (document.getElementById("org-form-day")) document.getElementById("org-form-day").value = org.meeting_day || "Rabu";



        if (document.getElementById("org-form-time")) document.getElementById("org-form-time").value = org.meeting_time || "2:00 - 4:00 Petang";



        if (document.getElementById("org-form-venue")) document.getElementById("org-form-venue").value = org.meeting_venue || "Sekolah";



        if (document.getElementById("org-form-vision")) document.getElementById("org-form-vision").value = org.vision_mission || "";



      }



    } else {



      const titleElem = document.getElementById("modal-org-title");



      if (titleElem) titleElem.textContent = "Tambah Organisasi Baharu";



      if (state.currentOrgTab && state.currentOrgTab !== "all" && document.getElementById("org-form-category")) {



        document.getElementById("org-form-category").value = state.currentOrgTab;



      }



      if (document.getElementById("org-form-color")) document.getElementById("org-form-color").value = "#1e3a8a";



      if (document.getElementById("org-form-color-text")) document.getElementById("org-form-color-text").value = "#1e3a8a";



      if (document.getElementById("org-form-day")) document.getElementById("org-form-day").value = "Rabu";



      if (document.getElementById("org-form-time")) document.getElementById("org-form-time").value = "2:00 - 4:00 Petang";



      if (document.getElementById("org-form-venue")) document.getElementById("org-form-venue").value = "Sekolah";



    }







    modal.classList.remove("hidden");



    if (typeof lucide !== 'undefined') lucide.createIcons();



  },







  injectOrgModalDOM() {



    if (document.getElementById("modal-org")) return;



    const modalHtml = `



      <div id="modal-org" class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">



        <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95">



          <div class="p-4 sm:p-5 bg-navy-900 text-white flex items-center justify-between">



            <div class="flex items-center space-x-2">



              <i data-lucide="layers" class="w-5 h-5 text-blue-400"></i>



              <h3 id="modal-org-title" class="text-sm sm:text-base font-bold">Tambah Organisasi Baharu</h3>



            </div>



            <button type="button" onclick="app.closeModal('modal-org')" class="text-slate-300 hover:text-white p-1">



              <i data-lucide="x" class="w-5 h-5"></i>



            </button>



          </div>



          <form id="form-org" onsubmit="app.saveOrganization(event)" class="p-5 space-y-4 text-xs">



            <input type="hidden" id="org-form-id">



            <div>



              <label class="block font-bold text-slate-700 uppercase mb-1">Nama Organisasi / Kelab / Sukan *</label>



              <input type="text" id="org-form-name" required placeholder="cth: Kelab Robotik & Inovasi / Kelab Ping Pong" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



            </div>







            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">



              <div>



                <label class="block font-bold text-slate-700 uppercase mb-1">Kategori Kokurikulum *</label>



                <select id="org-form-category" required class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



                  <option value="Rumah Sukan">Rumah Sukan</option>



                  <option value="Unit Beruniform">Unit Beruniform</option>



                  <option value="Kelab & Persatuan">Kelab & Persatuan</option>



                  <option value="Sukan & Permainan">Sukan & Permainan</option>



                </select>



              </div>



              <div>



                <label class="block font-bold text-slate-700 uppercase mb-1">Warna Tema</label>



                <div class="flex items-center space-x-2">



                  <input type="color" id="org-form-color" value="#1e3a8a" onchange="document.getElementById('org-form-color-text').value = this.value" class="w-9 h-9 p-0.5 rounded-lg border border-slate-300 cursor-pointer">



                  <input type="text" id="org-form-color-text" placeholder="#1e3a8a" value="#1e3a8a" oninput="document.getElementById('org-form-color').value = this.value" class="flex-1 py-2 px-3 border border-slate-300 rounded-xl outline-none font-mono text-[11px]">



                </div>



              </div>



            </div>







            <div>



              <label class="block font-bold text-slate-700 uppercase mb-1">Guru Penasihat / Jurulatih</label>



              <input type="text" id="org-form-advisors" placeholder="cth: Pn. Faridah binti Kassim & En. Shahril" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none">



            </div>







            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">



              <div>



                <label class="block font-bold text-slate-700 uppercase mb-1">Hari Perjumpaan</label>



                <input type="text" id="org-form-day" placeholder="cth: Rabu / Khamis" value="Rabu" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none">



              </div>



              <div>



                <label class="block font-bold text-slate-700 uppercase mb-1">Masa</label>



                <input type="text" id="org-form-time" placeholder="cth: 2:00 - 4:00 PM" value="2:00 - 4:00 Petang" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none">



              </div>



              <div>



                <label class="block font-bold text-slate-700 uppercase mb-1">Tempat</label>



                <input type="text" id="org-form-venue" placeholder="cth: Makmal Komputer" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none">



              </div>



            </div>







            <div>



              <label class="block font-bold text-slate-700 uppercase mb-1">Visi / Misi / Keterangan Ringkas</label>



              <textarea id="org-form-vision" rows="2" placeholder="Objektif penubuhan, kemahiran dan aktiviti kelab..." class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none"></textarea>



            </div>







            <div class="flex justify-end space-x-2 pt-2 border-t border-slate-200">



              <button type="button" onclick="app.closeModal('modal-org')" class="px-4 py-2 bg-slate-200 text-slate-700 font-semibold rounded-xl">Batal</button>



              <button type="submit" id="btn-save-org" class="px-4 py-2 bg-navy-800 hover:bg-navy-900 text-white font-bold rounded-xl flex items-center space-x-1.5 shadow-sm">



                <i data-lucide="save" class="w-4 h-4"></i>



                <span>Simpan Organisasi</span>



              </button>



            </div>



          </form>



        </div>



      </div>



    `;



    document.body.insertAdjacentHTML('beforeend', modalHtml);



  },







  async saveOrganization(e) {



    e.preventDefault();



    const id = document.getElementById("org-form-id").value;



    const name = document.getElementById("org-form-name").value.trim();



    const category = document.getElementById("org-form-category").value;



    const colorCode = document.getElementById("org-form-color").value.trim() || "#1e3a8a";



    const advisors = document.getElementById("org-form-advisors").value.trim();



    const day = document.getElementById("org-form-day").value.trim() || "Rabu";



    const time = document.getElementById("org-form-time").value.trim() || "2:00 - 4:00 Petang";



    const venue = document.getElementById("org-form-venue").value.trim() || "Sekolah";



    const vision = document.getElementById("org-form-vision").value.trim();







    if (!name) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila masukkan nama organisasi.' });



      return;



    }







    const payload = {



      name: name,



      category: category,



      color_code: colorCode,



      advisor_teachers: advisors,



      meeting_day: day,



      meeting_time: time,



      meeting_venue: venue,



      vision_mission: vision,



      status: "Aktif",



      academic_year: "2026/2027"



    };







    try {



      let res;



      if (id) {



        res = await fetch(`/api/organizations/${id}`, {



          method: "PUT",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      } else {



        res = await fetch("/api/organizations", {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      }







      if (res.ok) {



        this.closeModal("modal-org");



        Swal.fire({



          icon: 'success',



          title: 'Berjaya',



          text: id ? 'Maklumat organisasi berjaya dikemas kini!' : `Organisasi ${name} berjaya ditambah!`,



          timer: 2000,



          showConfirmButton: false



        });



        await this.fetchOrganizations();



        this.renderOrganizations();



        await this.loadDashboard();



      } else {



        const err = await res.json();



        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal menyimpan organisasi.' });



      }



    } catch (err) {



      console.error(err);



      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa menyimpan organisasi.' });



    }



  },







  async deleteOrg(orgId, name = null) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk memadam organisasi. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    if (!name) {



      const o = state.organizations?.find(x => x.id === orgId);



      name = o ? o.name : 'organisasi ini';



    }



    const res = await Swal.fire({



      title: 'Adakah anda pasti?',



      text: `Padam organisasi ${name}?`,



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#dc2626',



      confirmButtonText: 'Ya, Padam'



    });







    if (res.isConfirmed) {



      try {



        const response = await fetch(`/api/organizations/${orgId}`, { method: "DELETE" });



        if (response.ok) {



          Swal.fire({ icon: 'success', title: 'Dipadam', timer: 1500, showConfirmButton: false });



          await this.fetchOrganizations();



          this.renderOrganizations();



        }



      } catch (e) {



        console.error(e);



      }



    }



  },







  async openOrgManageModal(orgId) {



    try {



      state.currentManagingOrgId = orgId;



      const res = await fetch(`/api/organizations/${orgId}`);



      if (!res.ok) return;



      const org = await res.json();



      state.currentManagingOrg = org;







      document.getElementById("manage-org-title").textContent = org.name.toUpperCase();



      document.getElementById("manage-org-category").textContent = `${org.category} • Guru Penasihat: ${org.advisor_teachers || '-'}`;







      const body = document.getElementById("manage-org-body");



      body.innerHTML = `



        <!-- Top Toolbar: Add Member / Assign AJK -->



        <div class="p-3 bg-slate-100 rounded-xl flex flex-wrap items-center justify-between gap-3">



          <div class="text-xs font-bold text-slate-800">Senarai Ahli Murid (${org.members.length} Orang)</div>



          <div class="flex items-center space-x-2">



            <button onclick="app.promptAddMemberToOrg(${org.id})" class="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold text-xs flex items-center space-x-1 shadow-xs">



              <i data-lucide="user-plus" class="w-3.5 h-3.5"></i>



              <span>Tambah Ahli</span>



            </button>



          </div>



        </div>







        <!-- Jawatankuasa / Committees Structure Visual -->



        <div>



          <h4 class="font-bold text-navy-900 mb-2 uppercase text-xs">Jawatankuasa Murid (AJK)</h4>



          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">



            ${org.committees.map(c => `



              <div class="p-3 bg-white border border-slate-200 rounded-xl text-center shadow-xs">



                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">${c.position}</span>



                <div class="text-xs font-bold text-slate-800 mt-1.5">${c.student_name}</div>



                <div class="text-[10px] text-slate-500">${c.class_name}</div>



                ${this.canDelete() ? `<button onclick="app.removeAjkPosition(${org.id}, ${c.student_id})" class="text-[10px] text-rose-600 font-semibold hover:underline mt-1">Gugur</button>` : ''}



              </div>



            `).join("")}



          </div>



        </div>







        <!-- Members Table -->



        <div>



          <h4 class="font-bold text-navy-900 mb-2 uppercase text-xs">Senarai Keseluruhan Ahli & Lantikan Jawatan</h4>



          <div class="border border-slate-200 rounded-xl overflow-hidden">



            <table class="w-full text-left text-xs">



              <thead class="bg-slate-100 font-bold">



                <tr>



                  <th class="p-2.5">Nama Murid</th>



                  <th class="p-2.5">Kelas</th>



                  <th class="p-2.5">Jawatan AJK</th>



                  <th class="p-2.5 text-center">Tindakan</th>



                </tr>



              </thead>



              <tbody class="divide-y divide-slate-200">



                ${org.members.map(m => `



                  <tr>



                    <td class="p-2.5 font-bold">${m.full_name}</td>



                    <td class="p-2.5">${m.class_name}</td>



                    <td class="p-2.5">



                      <select onchange="app.assignAjkPosition(${org.id}, ${m.id}, this.value)" class="py-1 px-2 border border-slate-300 rounded-lg text-xs outline-none font-semibold ${m.committee_position ? 'bg-amber-50 text-amber-900 border-amber-300' : ''}">



                        <option value="">-- Ahli Biasa --</option>



                        <option value="Pengerusi" ${m.committee_position === 'Pengerusi' ? 'selected' : ''}>Pengerusi / Ketua Rumah</option>



                        <option value="Naib Pengerusi" ${m.committee_position === 'Naib Pengerusi' ? 'selected' : ''}>Naib Pengerusi / Penolong</option>



                        <option value="Setiausaha" ${m.committee_position === 'Setiausaha' ? 'selected' : ''}>Setiausaha</option>



                        <option value="Penolong Setiausaha" ${m.committee_position === 'Penolong Setiausaha' ? 'selected' : ''}>Penolong Setiausaha</option>



                        <option value="Bendahari" ${m.committee_position === 'Bendahari' ? 'selected' : ''}>Bendahari</option>



                        <option value="Penolong Bendahari" ${m.committee_position === 'Penolong Bendahari' ? 'selected' : ''}>Penolong Bendahari</option>



                        <option value="Ahli Jawatankuasa" ${m.committee_position === 'Ahli Jawatankuasa' ? 'selected' : ''}>Ahli Jawatankuasa (AJK)</option>



                      </select>



                    </td>



                    <td class="p-2.5 text-center">



                      ${this.canDelete() ? `



                      <button onclick="app.removeMemberFromOrg(${org.id}, ${m.id})" class="text-rose-600 hover:text-rose-800 text-xs font-bold">Keluarkan</button>



                      ` : '<span class="text-slate-400 text-xs">-</span>'}



                    </td>



                  </tr>



                `).join("")}



              </tbody>



            </table>



          </div>



        </div>



      `;







      document.getElementById("modal-org-manage").classList.remove("hidden");



      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async promptAddMemberToOrg(orgId) {



    await this.openAddMemberModal(orgId);



  },







  async openAddMemberModal(orgId) {



    try {



      await this.ensureStudentsLoaded(true);



      let org = state.currentManagingOrg;



      if (!org || org.id !== orgId) {



        const res = await fetch(`/api/organizations/${orgId}`);



        if (res.ok) {



          org = await res.json();



          state.currentManagingOrg = org;



        }



      }



      if (!org) return;







      state.addMemberSelectedStudentIds = new Set();







      const nameElem = document.getElementById("add-member-org-name");



      const badgeElem = document.getElementById("add-member-org-badge");



      const subtitleElem = document.getElementById("add-member-org-subtitle");



      if (nameElem) nameElem.textContent = org.name;



      if (badgeElem) badgeElem.textContent = org.category;



      if (subtitleElem) subtitleElem.textContent = `Pilih murid mengikut kelas untuk didaftarkan ke dalam ${org.name} (${org.category})`;







      // Populate Class Filter Dropdown



      const classFilter = document.getElementById("add-member-class-filter");



      if (classFilter) {



        const classes = Array.from(new Set((state.students || []).map(s => s.class_name).filter(Boolean))).sort();



        classFilter.innerHTML = `<option value="">-- Semua Kelas (${state.students.length} Murid) --</option>` +



          classes.map(c => `<option value="${c}">${c}</option>`).join("");



        classFilter.value = "";



      }







      const searchInput = document.getElementById("add-member-search-input");



      if (searchInput) searchInput.value = "";







      this.renderAddMemberStudentsList();







      const modal = document.getElementById("modal-add-org-member");



      if (modal) {



        modal.classList.remove("hidden");



        lucide.createIcons();



      }



    } catch (err) {



      console.error("openAddMemberModal error:", err);



    }



  },







  renderAddMemberStudentsList() {



    const org = state.currentManagingOrg;



    const container = document.getElementById("add-member-students-container");



    if (!container || !org) return;







    const classFilter = document.getElementById("add-member-class-filter")?.value || "";



    const searchFilter = (document.getElementById("add-member-search-input")?.value || "").toLowerCase().trim();







    const cat = (org.category || "").toLowerCase();



    let idProp = "sport_house_id";



    let nameProp = "sport_house_name";



    let catLabel = "Rumah Sukan";







    if (cat.includes("uniform")) {



      idProp = "uniform_unit_id";



      nameProp = "uniform_unit_name";



      catLabel = "Unit Beruniform";



    } else if (cat.includes("kelab") || cat.includes("persatuan")) {



      idProp = "club_society_id";



      nameProp = "club_society_name";



      catLabel = "Kelab & Persatuan";



    } else if (cat.includes("sukan") || cat.includes("permainan")) {



      idProp = "sports_game_id";



      nameProp = "sports_game_name";



      catLabel = "Sukan & Permainan";



    }







    const currentOrgMemberIds = new Set((org.members || []).map(m => m.id));







    const filtered = (state.students || []).filter(s => {



      if (classFilter && s.class_name !== classFilter) return false;



      if (searchFilter) {



        const matchName = (s.full_name || "").toLowerCase().includes(searchFilter);



        const matchIc = (s.ic_number || "").toLowerCase().includes(searchFilter);



        if (!matchName && !matchIc) return false;



      }



      return true;



    });







    if (filtered.length === 0) {



      container.innerHTML = `



        <div class="p-8 text-center text-slate-400">



          <i data-lucide="users" class="w-8 h-8 mx-auto mb-2 opacity-50"></i>



          <p class="text-xs">Tiada rekod murid ditemui bagi kriteria carian atau kelas ini.</p>



        </div>



      `;



      lucide.createIcons();



      this.updateAddMemberCount();



      return;



    }







    container.innerHTML = filtered.map(s => {



      const assignedId = s[idProp];



      const assignedName = s[nameProp] || "Unit Lain";



      const isCurrentOrg = currentOrgMemberIds.has(s.id) || assignedId === org.id;



      const isConflict = assignedId && assignedId !== org.id;



      const isSelected = state.addMemberSelectedStudentIds.has(s.id);







      if (isConflict) {



        return `



          <div class="relative group p-2.5 bg-slate-200/90 border border-slate-300 rounded-xl flex items-center justify-between text-slate-500 opacity-70 cursor-not-allowed select-none transition hover:opacity-100 hover:bg-slate-300 shadow-2xs"



               title="Telah didaftarkan di: ${assignedName}. Murid tidak boleh berada dalam 2 unit berbeza bagi kategori ${catLabel}.">



            



            <!-- Window Kecil / Tooltip Info Apabila Cursor Dekat Nama -->



            <div class="pointer-events-none absolute left-6 bottom-full mb-1.5 hidden group-hover:flex z-50 flex-col bg-slate-900 text-white text-xs rounded-xl py-2 px-3 shadow-2xl border border-slate-700 min-w-[260px] animate-in fade-in zoom-in-95">



              <div class="flex items-center gap-1.5 font-bold text-amber-300">



                <i data-lucide="alert-triangle" class="w-3.5 h-3.5"></i>



                <span>Makluman Sekatan Unit</span>



              </div>



              <div class="text-slate-100 font-semibold mt-1">



                Murid ini telah didaftarkan di:



              </div>



              <div class="text-amber-200 font-black text-[13px] bg-slate-800 px-2 py-0.5 rounded mt-0.5 border border-slate-700 inline-block">



                ${assignedName}



              </div>



              <div class="text-[10px] text-slate-300 mt-1 border-t border-slate-700 pt-1">



                Peraturan: Tidak boleh murid yang sama berada di dalam ${catLabel} berbeza.



              </div>



            </div>







            <div class="flex items-center space-x-3">



              <input type="checkbox" disabled class="w-4 h-4 text-slate-400 bg-slate-200 border-slate-400 rounded cursor-not-allowed opacity-50">



              <div>



                <div class="flex items-center gap-2">



                  <span class="font-bold text-slate-700 line-through decoration-slate-400 cursor-help">${s.full_name}</span>



                  <span class="text-[10px] font-semibold text-slate-500 bg-slate-300/80 px-1.5 py-0.5 rounded">${s.gender || '-'}</span>



                </div>



                <div class="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">



                  <span>Kelas: <strong class="text-slate-700">${s.class_name || '-'}</strong></span>



                  <span>•</span>



                  <span>KP: <strong class="font-mono text-slate-700">${s.ic_number || '-'}</strong></span>



                </div>



              </div>



            </div>







            <div class="flex items-center space-x-2">



              <span class="text-[10px] font-bold bg-slate-300/90 text-slate-800 px-2.5 py-1 rounded-full flex items-center gap-1 border border-slate-400/60 shadow-2xs">



                <i data-lucide="lock" class="w-3 h-3 text-slate-600"></i>



                <span>${assignedName}</span>



              </span>



            </div>



          </div>



        `;



      } else if (isCurrentOrg) {



        return `



          <div class="p-2.5 bg-blue-50/70 border border-blue-200 rounded-xl flex items-center justify-between text-slate-700 select-none">



            <div class="flex items-center space-x-3">



              <input type="checkbox" checked disabled class="w-4 h-4 text-blue-600 bg-blue-100 border-blue-300 rounded cursor-not-allowed">



              <div>



                <div class="flex items-center gap-2">



                  <span class="font-bold text-blue-950">${s.full_name}</span>



                  <span class="text-[10px] font-semibold text-blue-800 bg-blue-100 px-1.5 py-0.5 rounded">${s.gender || '-'}</span>



                </div>



                <div class="text-[11px] text-blue-700 flex items-center gap-2 mt-0.5">



                  <span>Kelas: <strong class="text-blue-900">${s.class_name || '-'}</strong></span>



                  <span>•</span>



                  <span>KP: <strong class="font-mono text-blue-900">${s.ic_number || '-'}</strong></span>



                </div>



              </div>



            </div>







            <div>



              <span class="text-[10px] font-bold bg-blue-100 text-blue-800 px-2.5 py-1 rounded-full border border-blue-200">



                Ahli Sedia Ada



              </span>



            </div>



          </div>



        `;



      } else {



        return `



          <div onclick="app.toggleAddMemberStudent(${s.id})"



               class="p-2.5 bg-white hover:bg-emerald-50/80 border ${isSelected ? 'border-emerald-500 ring-1 ring-emerald-500 bg-emerald-50/50' : 'border-slate-200'} rounded-xl flex items-center justify-between text-slate-800 cursor-pointer transition shadow-2xs">



            <div class="flex items-center space-x-3">



              <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); app.toggleAddMemberStudent(${s.id});" class="w-4 h-4 text-emerald-600 bg-white border-slate-300 rounded focus:ring-emerald-500 cursor-pointer">



              <div>



                <div class="flex items-center gap-2">



                  <span class="font-bold ${isSelected ? 'text-emerald-950' : 'text-slate-900'}">${s.full_name}</span>



                  <span class="text-[10px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">${s.gender || '-'}</span>



                </div>



                <div class="text-[11px] text-slate-500 flex items-center gap-2 mt-0.5">



                  <span>Kelas: <strong class="text-slate-700">${s.class_name || '-'}</strong></span>



                  <span>•</span>



                  <span>KP: <strong class="font-mono text-slate-700">${s.ic_number || '-'}</strong></span>



                </div>



              </div>



            </div>







            <div>



              <span class="text-[10px] font-bold ${isSelected ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-800'} px-2.5 py-1 rounded-full transition">



                ${isSelected ? 'Dipilih' : 'Boleh Dipilih'}



              </span>



            </div>



          </div>



        `;



      }



    }).join("");







    lucide.createIcons();



    this.updateAddMemberCount();



  },







  toggleAddMemberStudent(studentId) {



    if (state.addMemberSelectedStudentIds.has(studentId)) {



      state.addMemberSelectedStudentIds.delete(studentId);



    } else {



      state.addMemberSelectedStudentIds.add(studentId);



    }



    this.renderAddMemberStudentsList();



  },







  toggleSelectAllAddMember(select) {



    const org = state.currentManagingOrg;



    if (!org) return;







    if (!select) {



      state.addMemberSelectedStudentIds.clear();



      this.renderAddMemberStudentsList();



      return;



    }







    const classFilter = document.getElementById("add-member-class-filter")?.value || "";



    const searchFilter = (document.getElementById("add-member-search-input")?.value || "").toLowerCase().trim();







    const cat = (org.category || "").toLowerCase();



    let idProp = "sport_house_id";



    if (cat.includes("uniform")) idProp = "uniform_unit_id";



    else if (cat.includes("kelab") || cat.includes("persatuan")) idProp = "club_society_id";



    else if (cat.includes("sukan") || cat.includes("permainan")) idProp = "sports_game_id";







    const currentOrgMemberIds = new Set((org.members || []).map(m => m.id));







    (state.students || []).forEach(s => {



      if (classFilter && s.class_name !== classFilter) return;



      if (searchFilter) {



        const matchName = (s.full_name || "").toLowerCase().includes(searchFilter);



        const matchIc = (s.ic_number || "").toLowerCase().includes(searchFilter);



        if (!matchName && !matchIc) return;



      }



      const isCurrentOrg = currentOrgMemberIds.has(s.id) || s[idProp] === org.id;



      const isConflict = s[idProp] && s[idProp] !== org.id;



      if (!isCurrentOrg && !isConflict) {



        state.addMemberSelectedStudentIds.add(s.id);



      }



    });







    this.renderAddMemberStudentsList();



  },







  updateAddMemberCount() {



    const countElem = document.getElementById("add-member-selected-count");



    const btn = document.getElementById("btn-submit-add-members");



    const count = state.addMemberSelectedStudentIds.size;



    if (countElem) countElem.textContent = count;



    if (btn) btn.disabled = count === 0;



  },







  async submitAddOrgMembers() {



    const org = state.currentManagingOrg;



    if (!org) return;



    const selected = Array.from(state.addMemberSelectedStudentIds);



    if (selected.length === 0) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih sekurang-kurangnya seorang murid untuk didaftarkan.' });



      return;



    }







    try {



      const res = await fetch(`/api/organizations/${org.id}/members`, {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ student_ids: selected })



      });







      const data = await res.json();



      if (res.ok) {



        this.closeModal("modal-add-org-member");



        Swal.fire({



          icon: 'success',



          title: 'Pendaftaran Berjaya',



          text: `${selected.length} orang murid telah berjaya didaftarkan ke dalam ${org.name}.`,



          timer: 2000,



          showConfirmButton: false



        });



        await this.ensureStudentsLoaded(true);



        await this.fetchOrganizations();



        await this.openOrgManageModal(org.id);



      } else {



        Swal.fire({



          icon: 'error',



          title: 'Pendaftaran Disekat',



          text: data.detail || 'Gagal mendaftarkan ahli murid.'



        });



      }



    } catch (err) {



      console.error("submitAddOrgMembers error:", err);



      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa mendaftar murid.' });



    }



  },







  async assignAjkPosition(orgId, studentId, position) {



    try {



      if (!position) {



        await fetch(`/api/organizations/${orgId}/committee/${studentId}`, { method: "DELETE" });



      } else {



        await fetch(`/api/organizations/${orgId}/committee`, {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify({ student_id: studentId, position: position })



        });



      }



      this.openOrgManageModal(orgId);



    } catch (err) {



      console.error(err);



    }



  },







  async removeAjkPosition(orgId, studentId) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk menggugurkan jawatan AJK. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    try {



      await fetch(`/api/organizations/${orgId}/committee/${studentId}`, { method: "DELETE" });



      this.openOrgManageModal(orgId);



    } catch (e) {



      console.error(e);



    }



  },







  async removeMemberFromOrg(orgId, studentId) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk mengeluarkan ahli murid. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    try {



      await fetch(`/api/organizations/${orgId}/members/${studentId}`, { method: "DELETE" });



      this.openOrgManageModal(orgId);



      await this.fetchOrganizations();



    } catch (e) {



      console.error(e);



    }



  },







  printCurrentOrgChart() {



    if (state.currentManagingOrgId) {



      this.prepareReport("org_chart", { org_id: state.currentManagingOrgId });



    }



  },







  // ==========================================



  // VIEW 4: KEHADIRAN KOKURIKULUM



  // ==========================================



  async loadAttendanceSessions() {



    try {



      const orgId = document.getElementById("filter-att-org")?.value || "";



      const start = document.getElementById("filter-att-start")?.value || "";



      const end = document.getElementById("filter-att-end")?.value || "";







      let url = "/api/attendance/sessions?limit=100";



      if (orgId) url += `&org_id=${orgId}`;



      if (start) url += `&start_date=${start}`;



      if (end) url += `&end_date=${end}`;







      const res = await fetch(url);



      if (!res.ok) return;



      const sessions = await res.json();







      const tbody = document.getElementById("attendance-sessions-table-body");



      if (!tbody) return;







      if (sessions.length === 0) {



        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-400">Tiada rekod sesi kehadiran</td></tr>`;



        return;



      }







      tbody.innerHTML = sessions.map(ses => `



        <tr class="hover:bg-slate-50 transition">



          <td class="p-3.5">



            <div class="font-bold text-slate-900">${ses.session_date}</div>



            <div class="text-[11px] text-slate-500">${ses.start_time} - ${ses.end_time}</div>



          </td>



          <td class="p-3.5">



            <div class="font-bold text-navy-900">${ses.org_name}</div>



            <span class="text-[10px] font-semibold text-slate-500">${ses.org_category}</span>



          </td>



          <td class="p-3.5">



            <div class="font-semibold text-slate-800">${ses.activity_title}</div>



            <div class="text-[11px] text-slate-500"><i data-lucide="map-pin" class="w-3 h-3 inline"></i> ${ses.venue || 'Sekolah'}</div>



          </td>



          <td class="p-3.5 font-semibold text-slate-700">${ses.advisor_teacher || '-'}</td>



          <td class="p-3.5 text-center">



            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${ses.attendance_rate >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">



              ${ses.total_present}/${ses.total_enrolled} (${ses.attendance_rate}%)



            </span>



          </td>



          <td class="p-3.5 text-center">



            <div class="flex items-center justify-center space-x-1.5">



              <a href="/api/attendance/export/excel/${ses.id}" title="Muat Turun Excel" class="p-1.5 text-emerald-600 hover:bg-emerald-100 rounded-lg">



                <i data-lucide="file-spreadsheet" class="w-4 h-4"></i>



              </a>



              <button onclick="app.prepareReport('org_attendance', { org_id: ${ses.organization_id} })" title="Cetak Lembaran" class="p-1.5 text-blue-600 hover:bg-blue-100 rounded-lg">



                <i data-lucide="printer" class="w-4 h-4"></i>



              </button>



            </div>



          </td>



        </tr>



      `).join("");







      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async openNewAttendanceModal() {



    const modal = document.getElementById("modal-attendance");



    const today = new Date().toISOString().split("T")[0];



    document.getElementById("att-form-date").value = today;



    document.getElementById("att-form-venue").value = "Tapak Perhimpunan SK Sungai Dendang";



    document.getElementById("att-form-teacher").value = state.currentUser?.full_name || "";



    document.getElementById("att-form-title").value = "Perjumpaan Mingguan Unit Kokurikulum";







    const defaultOrgId = state.organizations[0]?.id;



    if (defaultOrgId) {



      document.getElementById("att-form-org").value = defaultOrgId;



      await this.loadStudentsForAttendance(defaultOrgId);



    }







    modal.classList.remove("hidden");



    lucide.createIcons();



  },







  async loadStudentsForAttendance(orgId) {



    if (!orgId) return;



    try {



      const res = await fetch(`/api/organizations/${orgId}/members`);



      if (!res.ok) return;



      state.currentAttendanceStudents = await res.json();







      const tbody = document.getElementById("att-students-list-body");



      if (state.currentAttendanceStudents.length === 0) {



        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-400">Tiada ahli didaftarkan dalam organisasi ini. Sila daftar ahli dahulu.</td></tr>`;



        return;



      }







      tbody.innerHTML = state.currentAttendanceStudents.map((s, idx) => `



        <tr>



          <td class="p-2.5 text-center text-slate-500">${idx + 1}</td>



          <td class="p-2.5 font-bold text-slate-800">${s.full_name}</td>



          <td class="p-2.5 text-slate-600">${s.class_name}</td>



          <td class="p-2.5">



            <select id="att-status-${s.id}" class="py-1 px-2 border border-slate-300 rounded-lg text-xs outline-none font-bold bg-white">



              <option value="Hadir" class="text-emerald-700">Hadir</option>



              <option value="Tidak Hadir" class="text-rose-700">Tidak Hadir</option>



              <option value="Lewat" class="text-amber-700">Lewat</option>



              <option value="Bersebab" class="text-blue-700">Bersebab</option>



            </select>



          </td>



          <td class="p-2.5">



            <input type="text" id="att-remarks-${s.id}" placeholder="Catatan jika ada" class="w-full py-1 px-2 border border-slate-200 rounded-lg text-xs outline-none">



          </td>



        </tr>



      `).join("");



    } catch (err) {



      console.error(err);



    }



  },







  setAllAttendanceStatus(status) {



    state.currentAttendanceStudents.forEach(s => {



      const el = document.getElementById(`att-status-${s.id}`);



      if (el) el.value = status;



    });



  },







  async saveAttendanceSession() {



    const orgId = parseInt(document.getElementById("att-form-org").value);



    const date = document.getElementById("att-form-date").value;



    const title = document.getElementById("att-form-title").value.trim();



    const venue = document.getElementById("att-form-venue").value.trim();



    const teacher = document.getElementById("att-form-teacher").value.trim();



    const notes = document.getElementById("att-form-notes").value.trim();







    if (!orgId || !date || !title) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila lengkapkan maklumat wajib sesi kehadiran.' });



      return;



    }







    const records = state.currentAttendanceStudents.map(s => {



      const statusEl = document.getElementById(`att-status-${s.id}`);



      const remarksEl = document.getElementById(`att-remarks-${s.id}`);



      return {



        student_id: s.id,



        status: statusEl ? statusEl.value : "Hadir",



        remarks: remarksEl ? remarksEl.value.trim() : null



      };



    });







    const payload = {



      organization_id: orgId,



      session_date: date,



      start_time: "14:00",



      end_time: "16:00",



      venue: venue || "Sekolah",



      activity_title: title,



      advisor_teacher: teacher,



      notes: notes,



      records: records



    };







    try {



      const res = await fetch("/api/attendance/sessions", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });







      if (res.ok) {



        this.closeModal("modal-attendance");



        Swal.fire({ icon: 'success', title: 'Berjaya', text: 'Kehadiran berjaya disimpan dan laporan draf dicipta!', timer: 2000, showConfirmButton: false });



        await this.loadAttendanceSessions();



        await this.loadDashboard();



      }



    } catch (err) {



      console.error(err);



    }



  },







  // ==========================================



  // VIEW 5: AKTIVITI & LAPORAN MINGGUAN



  // ==========================================



  async loadActivities() {



    try {



      const search = document.getElementById("filter-act-search")?.value || "";



      const orgId = document.getElementById("filter-act-org")?.value || "";



      const status = document.getElementById("filter-act-status")?.value || "";







      let url = "/api/activities?limit=100";



      if (search) url += `&search=${encodeURIComponent(search)}`;



      if (orgId) url += `&org_id=${orgId}`;



      if (status) url += `&status=${status}`;







      const res = await fetch(url);



      if (!res.ok) return;



      const activities = await res.json();



      state.activities = activities;







      const container = document.getElementById("activities-cards-container");



      if (!container) return;







      if (activities.length === 0) {



        container.innerHTML = `



          <div class="col-span-3 text-center py-12 text-slate-400">



            <i data-lucide="file-text" class="w-10 h-10 mx-auto mb-2 opacity-50"></i>



            Tiada laporan aktiviti ditemui



          </div>



        `;



        lucide.createIcons();



        return;



      }







      container.innerHTML = activities.map(act => `



        <div class="stat-card glass-card p-5 rounded-2xl flex flex-col justify-between">



          <div>



            <div class="flex items-center justify-between mb-2">



              <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">${act.org_name}</span>



              <span class="badge-status text-[10px] ${this.getStatusBadgeClass(act.status)}">${act.status}</span>



            </div>



            <h3 class="text-sm font-bold text-slate-900">${act.title}</h3>



            <p class="text-[11px] text-slate-500 mt-1 line-clamp-2">${act.description_rundown || act.objectives || 'Aktiviti mingguan kokurikulum SK Sungai Dendang.'}</p>



            



            <div class="mt-3 pt-3 border-t border-slate-100 space-y-1 text-[11px] text-slate-600">



              <div><span class="font-semibold text-slate-800">Tarikh:</span> ${act.activity_date} (${act.start_time} - ${act.end_time})</div>



              <div><span class="font-semibold text-slate-800">Tempat:</span> ${act.venue || 'Sekolah'}</div>



              <div><span class="font-semibold text-slate-800">Kehadiran:</span> ${act.attendees_count || 0} orang murid</div>



              ${act.review_remarks ? `<div class="p-2 bg-amber-50 rounded-lg text-amber-800 text-[10px] mt-1"><strong>Catatan Semakan:</strong> ${act.review_remarks}</div>` : ''}



            </div>



          </div>







          <!-- Workflow Action Buttons based on User Role -->



          <div class="pt-4 mt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">



            <div class="flex items-center space-x-1">



              ${this.renderActivityWorkflowActions(act)}



            </div>



            <div class="flex items-center space-x-1">



              <button onclick="app.openEditActivityModal(${act.id})" title="Kemaskini Laporan & Kehadiran" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg transition">



                <i data-lucide="edit-3" class="w-4 h-4"></i>



              </button>



              <button onclick="app.prepareReport('weekly_activity', { org_id: ${act.organization_id} })" title="Cetak Laporan Rasmi" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg transition">



                <i data-lucide="printer" class="w-4 h-4"></i>



              </button>



              ${this.canDelete() ? `



              <button onclick="app.deleteActivity(${act.id})" title="Padam Laporan" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg transition">



                <i data-lucide="trash-2" class="w-4 h-4"></i>



              </button>



              ` : ''}



            </div>



          </div>



        </div>



      `).join("");







      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  renderActivityWorkflowActions(act) {



    const role = state.activeRole;



    let buttons = "";







    if (act.status === "Draf") {



      buttons += `<button onclick="app.processActivityWorkflow(${act.id}, 'Dihantar')" class="px-2.5 py-1 bg-blue-700 text-white rounded-lg text-xs font-bold hover:bg-blue-800">Hantar</button>`;



    } else if (act.status === "Dihantar") {



      if (["Penyelaras Kokurikulum", "Setiausaha Kokurikulum", "GPK Kokurikulum", "Admin"].includes(role)) {



        buttons += `<button onclick="app.processActivityWorkflow(${act.id}, 'Disemak')" class="px-2.5 py-1 bg-cyan-700 text-white rounded-lg text-xs font-bold hover:bg-cyan-800">Semak</button>`;



        buttons += `<button onclick="app.processActivityWorkflowWithRemarks(${act.id}, 'Perlu Pindaan')" class="px-2 py-1 bg-amber-600 text-white rounded-lg text-xs font-bold hover:bg-amber-700">Pindaan</button>`;



      }



    } else if (act.status === "Disemak") {



      if (["GPK Kokurikulum", "Setiausaha Kokurikulum", "Admin"].includes(role)) {



        buttons += `<button onclick="app.processActivityWorkflow(${act.id}, 'Disahkan')" class="px-2.5 py-1 bg-emerald-700 text-white rounded-lg text-xs font-bold hover:bg-emerald-800">Sahkan</button>`;



        buttons += `<button onclick="app.processActivityWorkflowWithRemarks(${act.id}, 'Perlu Pindaan')" class="px-2 py-1 bg-amber-600 text-white rounded-lg text-xs font-bold hover:bg-amber-700">Pindaan</button>`;



      }



    } else if (act.status === "Perlu Pindaan") {



      buttons += `<button onclick="app.processActivityWorkflow(${act.id}, 'Dihantar')" class="px-2.5 py-1 bg-blue-700 text-white rounded-lg text-xs font-bold hover:bg-blue-800">Hantar Semula</button>`;



    }







    return buttons;



  },







  async processActivityWorkflow(activityId, status) {



    try {



      const res = await fetch(`/api/activities/${activityId}/action`, {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ status: status })



      });



      if (res.ok) {



        Swal.fire({ icon: 'success', title: 'Berjaya', text: `Status laporan ditukar kepada ${status}`, timer: 1500, showConfirmButton: false });



        this.loadActivities();



        this.loadDashboard();



      }



    } catch (e) {



      console.error(e);



    }



  },







  async processActivityWorkflowWithRemarks(activityId, status) {



    const { value: remarks } = await Swal.fire({



      title: 'Catatan / Alasan Pindaan',



      input: 'textarea',



      inputPlaceholder: 'Sila nyatakan perkara yang perlu diperbaiki oleh guru penasihat...',



      showCancelButton: true



    });







    if (remarks) {



      try {



        const res = await fetch(`/api/activities/${activityId}/action`, {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify({ status: status, remarks: remarks })



        });



        if (res.ok) {



          Swal.fire({ icon: 'success', title: 'Berjaya', text: 'Catatan pindaan telah dihantar kepada guru penasihat.', timer: 1500, showConfirmButton: false });



          this.loadActivities();



        }



      } catch (e) {



        console.error(e);



      }



    }



  },







  async deleteActivity(activityId) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk memadam laporan aktiviti. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    const act = (state.activities || []).find(a => a.id === activityId);



    const title = act ? act.title : `ID #${activityId}`;



    const confirm = await Swal.fire({



      title: 'Padam Laporan Aktiviti?',



      html: `Adakah anda pasti mahu memadamkan laporan aktiviti:<br><b class="text-rose-700 text-sm">"${title}"</b>?<br><br><span class="text-xs text-slate-500">Tindakan ini akan memadam rekod laporan aktiviti mingguan dan rekod kehadiran yang berkaitan.</span>`,



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#e11d48',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Padam',



      cancelButtonText: 'Batal'



    });







    if (!confirm.isConfirmed) return;







    try {



      const res = await fetch(`/api/activities/${activityId}`, {



        method: 'DELETE'



      });



      const data = await res.json();



      if (res.ok) {



        Swal.fire({



          icon: 'success',



          title: 'Dipadamkan',



          text: data.message || 'Laporan aktiviti berjaya dipadam.',



          timer: 1500,



          showConfirmButton: false



        });



        const modal = document.getElementById("modal-activity");



        if (modal && !modal.classList.contains("hidden")) {



          this.closeModal("modal-activity");



        }



        await this.loadActivities();



        await this.loadAttendanceSessions();



        await this.loadDashboard();



      } else {



        Swal.fire({



          icon: 'error',



          title: 'Ralat',



          text: data.detail || 'Gagal memadam laporan aktiviti.'



        });



      }



    } catch (err) {



      console.error(err);



      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat semasa memadam laporan aktiviti.' });



    }



  },







  deleteActivityFromModal() {



    const id = document.getElementById("act-form-id")?.value;



    if (id) {



      this.deleteActivity(parseInt(id));



    }



  },







  openNewActivityModal() {



    const modal = document.getElementById("modal-activity");



    const form = document.getElementById("form-activity");



    form.reset();



    document.getElementById("act-form-id").value = "";



    document.getElementById("modal-activity-title").textContent = "Laporan Aktiviti Mingguan & Rekod Kehadiran";



    document.getElementById("act-form-date").value = new Date().toISOString().split("T")[0];



    document.getElementById("act-form-venue").value = "Tapak Perhimpunan SK Sungai Dendang";



    document.getElementById("act-form-teacher").value = state.currentUser?.full_name || "Guru Penasihat";







    const btnDel = document.getElementById("btn-delete-activity-modal");



    if (btnDel) btnDel.classList.add("hidden");







    // Populate organization dropdown



    const orgSelect = document.getElementById("act-form-org");



    if (orgSelect && state.organizations) {



      orgSelect.innerHTML = state.organizations.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("");



      const defaultOrgId = state.organizations[0]?.id;



      if (defaultOrgId) {



        orgSelect.value = defaultOrgId;



        this.loadMembersForActivityForm(defaultOrgId);



      }



    }







    // Reset photo previews



    for (let i = 1; i <= 4; i++) {



      const preview = document.getElementById(`act-photo-${i}-preview`);



      const label = document.getElementById(`act-photo-${i}-label`);



      const urlInput = document.getElementById(`act-photo-${i}-url`);



      if (preview) { preview.src = ""; preview.classList.add("hidden"); }



      if (label) label.classList.remove("hidden");



      if (urlInput) urlInput.value = "";



    }







    modal.classList.remove("hidden");



    lucide.createIcons();



  },







  async loadMembersForActivityForm(orgId, existingRecords = []) {



    if (!orgId) return;



    try {



      const res = await fetch(`/api/organizations/${orgId}/members`);



      if (!res.ok) return;



      const members = await res.json();



      state.currentActivityMembers = members;







      const tbody = document.getElementById("act-att-members-table-body");



      if (!tbody) return;







      if (members.length === 0) {



        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-400">Tiada ahli berdaftar dalam organisasi ini. Sila tetapkan ahli di modul Organisasi.</td></tr>`;



        this.updateActivityAttendanceStats();



        return;



      }







      // Map existing records if editing



      const recordsMap = {};



      if (existingRecords && existingRecords.length > 0) {



        existingRecords.forEach(r => {



          recordsMap[r.student_id] = { status: r.status, remarks: r.remarks || "" };



        });



      }







      tbody.innerHTML = members.map((s, idx) => {



        const prev = recordsMap[s.id];



        const status = prev ? prev.status : "Hadir";



        const remarks = prev ? prev.remarks : "";







        return `



          <tr data-student-id="${s.id}" class="hover:bg-slate-50">



            <td class="p-2 text-center text-slate-500 font-bold">${idx + 1}</td>



            <td class="p-2">



              <div class="font-bold text-slate-800">${s.full_name}</div>



              <div class="text-[10px] text-slate-400 font-mono">${s.ic_number || ''}</div>



            </td>



            <td class="p-2 text-center text-slate-700 font-semibold">${s.class_name || '-'}</td>



            <td class="p-2">



              <select onchange="app.updateActivityAttendanceStats()" class="act-att-status-select w-full py-1 px-2 border border-slate-300 rounded-lg text-xs font-bold outline-none bg-white">



                <option value="Hadir" ${status === 'Hadir' ? 'selected' : ''} class="text-emerald-700 font-bold">Hadir</option>



                <option value="Tidak Hadir" ${status === 'Tidak Hadir' ? 'selected' : ''} class="text-rose-700 font-bold">Tidak Hadir</option>



                <option value="Kebenaran / Sakit" ${status.includes('Kebenaran') || status === 'Sakit' ? 'selected' : ''} class="text-amber-700 font-bold">Kebenaran / Sakit</option>



                <option value="Lewat" ${status === 'Lewat' ? 'selected' : ''} class="text-blue-700 font-bold">Lewat</option>



              </select>



            </td>



            <td class="p-2">



              <input type="text" value="${remarks}" placeholder="Catatan / sebab jika tidak hadir" class="act-att-remarks-input w-full py-1 px-2 border border-slate-200 rounded-lg text-xs outline-none focus:ring-1 focus:ring-navy-600">



            </td>



          </tr>



        `;



      }).join("");







      this.updateActivityAttendanceStats();



    } catch (err) {



      console.error(err);



    }



  },







  setActivityAllAttendance(status) {



    document.querySelectorAll(".act-att-status-select").forEach(sel => {



      sel.value = status;



    });



    this.updateActivityAttendanceStats();



  },







  updateActivityAttendanceStats() {



    const rows = document.querySelectorAll("#act-att-members-table-body tr[data-student-id]");



    const total = rows.length;



    let present = 0;



    let absent = 0;







    rows.forEach(r => {



      const val = r.querySelector(".act-att-status-select")?.value;



      if (val === "Hadir" || val === "Lewat") {



        present++;



      } else {



        absent++;



      }



    });







    const percent = total > 0 ? Math.round((present / total) * 100) : 0;







    const totalEl = document.getElementById("act-att-total");



    const presentEl = document.getElementById("act-att-present");



    const absentEl = document.getElementById("act-att-absent");



    const percentEl = document.getElementById("act-att-percent");







    if (totalEl) totalEl.textContent = total;



    if (presentEl) presentEl.textContent = present;



    if (absentEl) absentEl.textContent = absent;



    if (percentEl) percentEl.textContent = `${percent}%`;



  },







  async openEditActivityModal(id) {



    try {



      const res = await fetch(`/api/activities/${id}`);



      if (!res.ok) return;



      const act = await res.json();







      const modal = document.getElementById("modal-activity");



      document.getElementById("modal-activity-title").textContent = `Kemaskini Laporan: ${act.title}`;



      document.getElementById("act-form-id").value = act.id;







      const btnDel = document.getElementById("btn-delete-activity-modal");



      if (btnDel) {



        if (this.canDelete()) {



          btnDel.classList.remove("hidden");



        } else {



          btnDel.classList.add("hidden");



        }



      }



      document.getElementById("act-form-date").value = act.activity_date || '';



      document.getElementById("act-form-venue").value = act.venue || '';



      document.getElementById("act-form-title").value = act.title || '';



      document.getElementById("act-form-teacher").value = act.teachers_involved || '';



      document.getElementById("act-form-objectives").value = act.objectives || '';



      document.getElementById("act-form-rundown").value = act.description_rundown || '';



      document.getElementById("act-form-reflection").value = act.reflection || '';



      document.getElementById("act-form-suggestions").value = act.suggestions || '';







      const orgSelect = document.getElementById("act-form-org");



      if (orgSelect && state.organizations) {



        orgSelect.innerHTML = state.organizations.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("");



        orgSelect.value = act.organization_id;



      }







      await this.loadMembersForActivityForm(act.organization_id, act.attendance_records);







      // Photos



      for (let i = 1; i <= 4; i++) {



        const url = act[`photo_${i}`];



        const preview = document.getElementById(`act-photo-${i}-preview`);



        const label = document.getElementById(`act-photo-${i}-label`);



        const urlInput = document.getElementById(`act-photo-${i}-url`);



        if (urlInput) urlInput.value = url || '';



        if (preview && url) {



          preview.src = url;



          preview.classList.remove("hidden");



          if (label) label.classList.add("hidden");



        } else if (preview) {



          preview.src = '';



          preview.classList.add("hidden");



          if (label) label.classList.remove("hidden");



        }



      }







      modal.classList.remove("hidden");



      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async uploadActivityPhoto(input, photoIndex) {



    if (!input.files || input.files.length === 0) return;



    const formData = new FormData();



    formData.append("file", input.files[0]);







    try {



      const res = await fetch("/api/activities/upload-photo", { method: "POST", body: formData });



      if (res.ok) {



        const data = await res.json();



        document.getElementById(`act-photo-${photoIndex}-url`).value = data.url;



        const preview = document.getElementById(`act-photo-${photoIndex}-preview`);



        preview.src = data.url;



        preview.classList.remove("hidden");



        document.getElementById(`act-photo-${photoIndex}-label`).classList.add("hidden");



      }



    } catch (e) {



      console.error(e);



    }



  },







  async saveActivityReport(e) {



    e.preventDefault();



    const id = document.getElementById("act-form-id").value;







    const attendance_records = [];



    document.querySelectorAll("#act-att-members-table-body tr[data-student-id]").forEach(row => {



      const studentId = parseInt(row.getAttribute("data-student-id"));



      const status = row.querySelector(".act-att-status-select")?.value || "Hadir";



      const remarks = row.querySelector(".act-att-remarks-input")?.value?.trim() || null;



      if (studentId) {



        attendance_records.push({ student_id: studentId, status: status, remarks: remarks });



      }



    });







    const presentCount = attendance_records.filter(r => r.status === "Hadir" || r.status === "Lewat").length;







    const payload = {



      organization_id: parseInt(document.getElementById("act-form-org").value),



      activity_date: document.getElementById("act-form-date").value,



      start_time: "14:00",



      end_time: "16:00",



      venue: document.getElementById("act-form-venue").value.trim() || "Sekolah",



      title: document.getElementById("act-form-title").value.trim(),



      objectives: document.getElementById("act-form-objectives").value.trim(),



      description_rundown: document.getElementById("act-form-rundown").value.trim(),



      teachers_involved: document.getElementById("act-form-teacher").value.trim() || (state.currentUser?.full_name || "Guru Penasihat"),



      attendees_count: presentCount,



      reflection: document.getElementById("act-form-reflection").value.trim(),



      suggestions: document.getElementById("act-form-suggestions").value.trim(),



      photo_1: document.getElementById("act-photo-1-url").value || null,



      photo_2: document.getElementById("act-photo-2-url").value || null,



      photo_3: document.getElementById("act-photo-3-url").value || null,



      photo_4: document.getElementById("act-photo-4-url").value || null,



      status: "Draf",



      attendance_records: attendance_records



    };







    try {



      let res;



      if (id) {



        res = await fetch(`/api/activities/${id}`, {



          method: "PUT",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      } else {



        res = await fetch("/api/activities", {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      }







      if (res.ok) {



        this.closeModal("modal-activity");



        Swal.fire({ icon: 'success', title: 'Berjaya Disimpan', text: 'Laporan aktiviti mingguan dan rekod kehadiran murid telah berjaya disimpan!', timer: 2000, showConfirmButton: false });



        await this.loadActivities();



        await this.loadAttendanceSessions();



        await this.loadDashboard();



      } else {



        const err = await res.json();



        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal menyimpan laporan aktiviti.' });



      }



    } catch (err) {



      console.error(err);



    }



  },







  // ==========================================



  // ==========================================



  // VIEW 6: SURAT KEBENARAN MURID (RO1 / RO2 / AKUAN KESIHATAN)



  // ==========================================



  async loadPermissionLetters() {



    try {



      const res = await fetch("/api/permission-letters");



      if (!res.ok) return;



      const letters = await res.json();







      const container = document.getElementById("permission-letters-container");



      if (!container) return;







      if (letters.length === 0) {



        container.innerHTML = `



          <div class="col-span-3 text-center py-12 text-slate-400">



            <i data-lucide="mail" class="w-10 h-10 mx-auto mb-2 opacity-50"></i>



            Tiada surat kebenaran dijana setakat ini. Klik butang 'Jana Surat Kebenaran' untuk mula.



          </div>



        `;



        lucide.createIcons();



        return;



      }







      container.innerHTML = letters.map(let => `



        <div class="stat-card glass-card p-5 rounded-2xl flex flex-col justify-between">



          <div>



            <div class="flex items-center justify-between mb-1.5">



              <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-900 border border-blue-200 font-mono">${let.letter_no || 'SKSD/KOKO'}</span>



              <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">${let.allowed_count || 0}/${let.total_students || 0} Dibenarkan</span>



            </div>



            <h3 class="text-sm font-bold text-slate-900 mt-2 line-clamp-2">${let.program_name}</h3>



            <div class="mt-3 pt-3 border-t border-slate-100 space-y-1.5 text-[11px] text-slate-600">



              <div><span class="font-semibold text-slate-800">Tempat:</span> ${let.destination_venue}</div>



              <div><span class="font-semibold text-slate-800">Penganjur:</span> ${let.organizer || '-'}</div>



              <div><span class="font-semibold text-slate-800">Tarikh:</span> ${let.start_datetime} - ${let.end_datetime}</div>



              <div><span class="font-semibold text-slate-800">Pengiring:</span> ${let.accompanying_teachers || '-'}</div>



              <div><span class="font-semibold text-slate-800">Yuran & Hubungan:</span> RM ${(let.fee_amount || 0).toFixed(2)} • ${let.contact_phone || '-'}</div>



              <div><span class="font-semibold text-slate-800">Murid Terlibat:</span> <strong class="text-navy-900">${let.total_students || 0} orang</strong></div>



            </div>



          </div>







          <div class="pt-4 mt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">



            <button onclick="app.openConsentTracker(${let.id})" class="px-2.5 py-1.5 bg-blue-50 text-blue-800 hover:bg-blue-100 rounded-xl text-xs font-bold flex items-center space-x-1 border border-blue-200 transition">



              <i data-lucide="check-square" class="w-3.5 h-3.5"></i>



              <span>Status Akuan (${let.allowed_count || 0}/${let.total_students || 0})</span>



            </button>



            <div class="flex items-center space-x-1">



              <button onclick="app.openLetterPrintOptionsModal(${let.id})" title="Cetak Surat (Pilihan RO1 / RO2 / Kesihatan)" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg transition">



                <i data-lucide="printer" class="w-4 h-4"></i>



              </button>



              <button onclick="app.openEditPermissionLetterModal(${let.id})" title="Kemaskini Surat & Senarai Murid" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg transition">



                <i data-lucide="edit-3" class="w-4 h-4"></i>



              </button>



              ${this.canDelete() ? `



              <button onclick="app.deletePermissionLetter(${let.id})" title="Padam / Buang Surat" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg transition">



                <i data-lucide="trash-2" class="w-4 h-4"></i>



              </button>



              ` : ''}



            </div>



          </div>



        </div>



      `).join("");







      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async ensureStudentsLoaded(forceReload = false) {



    if (forceReload || !state.students || state.students.length === 0) {



      try {



        const res = await fetch("/api/students?limit=500");



        if (res.ok) {



          state.students = await res.json();



        }



      } catch (e) {



        console.error("Error loading students:", e);



      }



    }



    return state.students || [];



  },







  
  filterLetterOrgDropdown(category) {
    const orgSelect = document.getElementById("let-form-org");
    if (!orgSelect) return;
    const orgs = (state.organizations || []).filter(o => !category || category === 'Lain-lain' || o.category === category);
    orgSelect.innerHTML = `<option value="">-- Pilihan Pasukan / Organisasi --</option>` +
      orgs.map(o => `<option value="${o.id}">${o.name} (${o.category})</option>`).join("");
  },

  async openNewPermissionLetterModal() {




    const modal = document.getElementById("modal-permission-letter");



    const form = document.getElementById("form-permission-letter");



    form.reset();



    document.getElementById("letter-form-id").value = "";



    document.getElementById("modal-letter-title").textContent = "Jana Surat Kebenaran Murid Luar Sekolah";



    document.getElementById("let-form-transport").value = "Bas Sekolah Khas";



    document.getElementById("let-form-phone").value = state.schoolSettings?.phone || "05-8391234";
    if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = "Daerah";
    if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = "Sukan & Permainan";
    this.filterLetterOrgDropdown("Sukan & Permainan");







    if (document.getElementById("letter-student-search")) document.getElementById("letter-student-search").value = "";



    if (document.getElementById("letter-student-class-filter")) document.getElementById("letter-student-class-filter").value = "";



    if (document.getElementById("letter-student-org-filter")) document.getElementById("letter-student-org-filter").value = "";







    state.selectedLetterTeachers = [];



    if (state.currentUser?.full_name) {



      state.selectedLetterTeachers.push(state.currentUser.full_name);



    }



    await this.populateLetterTeacherPicker();







    state.currentLetterSelectedStudentIds = new Set();



    await this.populateLetterStudentPicker();







    modal.classList.remove("hidden");



    lucide.createIcons();



  },







  async openEditPermissionLetterModal(letterId) {



    try {



      const res = await fetch(`/api/permission-letters/${letterId}`);



      if (!res.ok) return;



      const letter = await res.json();







      const modal = document.getElementById("modal-permission-letter");



      document.getElementById("modal-letter-title").textContent = `Kemaskini Surat: ${letter.program_name}`;



      document.getElementById("letter-form-id").value = letter.id;



      document.getElementById("let-form-program").value = letter.program_name || '';



      document.getElementById("let-form-venue").value = letter.destination_venue || '';



      document.getElementById("let-form-organizer").value = letter.organizer || '';



      document.getElementById("let-form-start").value = letter.start_datetime || '';



      document.getElementById("let-form-end").value = letter.end_datetime || '';



      document.getElementById("let-form-transport").value = letter.transportation || 'Bas Sekolah';



      document.getElementById("let-form-fee").value = letter.fee_amount || 0;
      document.getElementById("let-form-phone").value = letter.contact_phone || '';
      if (document.getElementById("let-form-level")) document.getElementById("let-form-level").value = letter.participation_level || "Daerah";
      if (document.getElementById("let-form-category")) document.getElementById("let-form-category").value = letter.activity_category || "Sukan & Permainan";
      this.filterLetterOrgDropdown(letter.activity_category || "Sukan & Permainan");
      if (document.getElementById("let-form-org")) document.getElementById("let-form-org").value = letter.represented_org_id || "";







      if (document.getElementById("letter-student-search")) document.getElementById("letter-student-search").value = "";



      if (document.getElementById("letter-student-class-filter")) document.getElementById("letter-student-class-filter").value = "";



      if (document.getElementById("letter-student-org-filter")) document.getElementById("letter-student-org-filter").value = "";







      state.selectedLetterTeachers = (letter.accompanying_teachers || '')



        .split(/[&,;]|\bdan\b/i)



        .map(t => t.trim())



        .filter(Boolean)



        .slice(0, 3);



      await this.populateLetterTeacherPicker();







      state.currentLetterSelectedStudentIds = new Set((letter.students || []).map(st => st.student_id));



      await this.populateLetterStudentPicker();







      modal.classList.remove("hidden");



      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async populateLetterTeacherPicker() {



    if (!state.teachers || state.teachers.length === 0) {



      await this.fetchTeachers();



    }



    const container = document.getElementById("let-teachers-list-container");



    const tagsContainer = document.getElementById("let-selected-teachers-tags");



    const counterElem = document.getElementById("let-teachers-counter");



    const hiddenInput = document.getElementById("let-form-teachers");



    if (!container) return;







    if (!state.selectedLetterTeachers) state.selectedLetterTeachers = [];







    // Sync Hidden Input



    if (hiddenInput) {



      hiddenInput.value = state.selectedLetterTeachers.join(" & ");



    }







    // Render Selected Tags



    if (tagsContainer) {



      if (state.selectedLetterTeachers.length === 0) {



        tagsContainer.innerHTML = `<span class="text-xs text-slate-400 italic">Sila tandakan nama guru di bawah (maksimum 3 cikgu).</span>`;



      } else {



        tagsContainer.innerHTML = state.selectedLetterTeachers.map((t, idx) => `



          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-100 text-blue-900 rounded-lg text-xs font-bold border border-blue-200 shadow-2xs">



            <span>${idx + 1}. ${t}</span>



            <button type="button" onclick="app.removeLetterTeacher('${t.replace(/'/g, "\\'")}')" class="text-blue-600 hover:text-rose-600 font-bold ml-1">



              <i data-lucide="x" class="w-3.5 h-3.5"></i>



            </button>



          </span>



        `).join("");



      }



    }







    // Update Counter



    if (counterElem) {



      counterElem.textContent = `${state.selectedLetterTeachers.length} / 3 dipilih`;



      if (state.selectedLetterTeachers.length >= 3) {



        counterElem.className = "text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300";



      } else {



        counterElem.className = "text-[11px] font-bold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200";



      }



    }







    // Render Teacher Checklist



    const isMaxReached = state.selectedLetterTeachers.length >= 3;



    container.innerHTML = (state.teachers || []).map(t => {



      const isSelected = state.selectedLetterTeachers.includes(t.name);



      const isDisabled = !isSelected && isMaxReached;



      return `



        <div onclick="${isDisabled ? '' : `app.toggleLetterTeacher('${t.name.replace(/'/g, "\\'")}')`}"



             class="flex items-center justify-between p-2 rounded-lg border text-xs transition ${



               isSelected ? 'bg-blue-50 border-blue-300 text-blue-950 font-bold shadow-2xs' :



               isDisabled ? 'bg-slate-100/70 border-slate-200 text-slate-400 cursor-not-allowed opacity-60' :



               'bg-white border-slate-200 hover:bg-slate-50 text-slate-700 cursor-pointer shadow-2xs'



             }">



          <div class="flex items-center space-x-2">



            <input type="checkbox" ${isSelected ? 'checked' : ''} ${isDisabled ? 'disabled' : ''}



                   onclick="event.stopPropagation(); app.toggleLetterTeacher('${t.name.replace(/'/g, "\\'")}')"



                   class="w-3.5 h-3.5 text-blue-600 rounded border-slate-300">



            <span>${t.name}</span>



          </div>



          <span class="text-[10px] text-slate-500">${t.designation || 'Guru'}</span>



        </div>



      `;



    }).join("");







    lucide.createIcons();



  },







  toggleLetterTeacher(name) {



    if (!state.selectedLetterTeachers) state.selectedLetterTeachers = [];



    const idx = state.selectedLetterTeachers.indexOf(name);



    if (idx >= 0) {



      state.selectedLetterTeachers.splice(idx, 1);



    } else {



      if (state.selectedLetterTeachers.length >= 3) {



        Swal.fire({



          icon: 'warning',



          title: 'Had Maksimum Dicapai',



          text: 'Pilihan guru pengiring dihadkan kepada maksimum 3 orang cikgu sahaja.',



          timer: 2000,



          showConfirmButton: false



        });



        return;



      }



      state.selectedLetterTeachers.push(name);



    }



    this.populateLetterTeacherPicker();



  },







  removeLetterTeacher(name) {



    if (!state.selectedLetterTeachers) return;



    const idx = state.selectedLetterTeachers.indexOf(name);



    if (idx >= 0) {



      state.selectedLetterTeachers.splice(idx, 1);



      this.populateLetterTeacherPicker();



    }



  },







  async populateLetterStudentPicker() {



    await this.ensureStudentsLoaded();







    // Populate Class Filter



    const classFilter = document.getElementById("letter-student-class-filter");



    if (classFilter && state.students) {



      const distinctClasses = Array.from(new Set(state.students.map(s => s.class_name).filter(Boolean))).sort();



      classFilter.innerHTML = `<option value="">Semua Kelas (${distinctClasses.length})</option>` +



        distinctClasses.map(c => `<option value="${c}">${c}</option>`).join("");



    }







    // Populate Organization Filter



    const orgFilter = document.getElementById("letter-student-org-filter");



    if (orgFilter) {



      if (!state.organizations || Object.keys(state.organizations).length === 0) {



        await this.fetchOrganizations();



      }



      const allOrgs = (state.organizations?.uniform_units || [])



        .concat(state.organizations?.clubs_societies || [])



        .concat(state.organizations?.sports_games || [])



        .concat(state.organizations?.sport_houses || []);







      orgFilter.innerHTML = `<option value="">Semua Organisasi / Sukan</option>` +



        allOrgs.map(o => `<option value="${o.name}">[${o.category}] ${o.name}</option>`).join("");



    }







    this.filterLetterStudentsPicker();



  },







  filterLetterStudentsPicker() {



    const search = (document.getElementById("letter-student-search")?.value || "").toLowerCase().trim();



    const classVal = document.getElementById("letter-student-class-filter")?.value || "";



    const orgVal = (document.getElementById("letter-student-org-filter")?.value || "").toLowerCase().trim();







    const picker = document.getElementById("letter-students-picker");



    if (!picker) return;







    if (!state.students || state.students.length === 0) {



      picker.innerHTML = `<div class="p-4 text-center text-slate-500 text-xs">Tiada rekod murid ditemui dalam sistem.</div>`;



      this.updateLetterSelectedCount();



      return;



    }







    if (!state.currentLetterSelectedStudentIds) {



      state.currentLetterSelectedStudentIds = new Set();



    }







    const filtered = state.students.filter(s => {



      const matchSearch = !search || 



        (s.full_name && s.full_name.toLowerCase().includes(search)) ||



        (s.ic_number && s.ic_number.toLowerCase().includes(search));



      



      const matchClass = !classVal || s.class_name === classVal;







      const matchOrg = !orgVal ||



        (s.uniform_unit_name && s.uniform_unit_name.toLowerCase().includes(orgVal)) ||



        (s.club_society_name && s.club_society_name.toLowerCase().includes(orgVal)) ||



        (s.sport_game_name && s.sport_game_name.toLowerCase().includes(orgVal)) ||



        (s.sport_house_name && s.sport_house_name.toLowerCase().includes(orgVal));







      return matchSearch && matchClass && matchOrg;



    });







    if (filtered.length === 0) {



      picker.innerHTML = `<div class="p-4 text-center text-slate-500 text-xs">Tiada murid menepati carian atau tapisan ini.</div>`;



    } else {



      picker.innerHTML = filtered.map(s => `



        <label class="flex items-center justify-between p-2 hover:bg-white rounded-lg cursor-pointer text-xs border border-transparent hover:border-slate-200 transition select-none">



          <div class="flex items-center space-x-2.5">



            <input type="checkbox" name="letter-student-id" value="${s.id}" ${state.currentLetterSelectedStudentIds.has(s.id) ? 'checked' : ''} onchange="app.toggleLetterStudentCheckbox(${s.id}, this.checked)" class="w-4 h-4 rounded border-slate-300 text-navy-800 focus:ring-navy-600">



            <div>



              <span class="font-bold text-slate-900">${s.full_name}</span>



              <span class="text-[10px] text-slate-500 font-mono ml-2">KP: ${s.ic_number || '-'}</span>



            </div>



          </div>



          <div class="flex items-center space-x-2 shrink-0">



            <span class="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-bold">${s.class_name || '-'}</span>



            <span class="px-2 py-0.5 bg-blue-50 text-blue-800 rounded text-[10px] font-bold">${s.gender === 'Lelaki' ? 'L' : 'P'}</span>



          </div>



        </label>



      `).join("");



    }







    this.updateLetterSelectedCount();



  },







  toggleLetterStudentCheckbox(studentId, isChecked) {



    if (!state.currentLetterSelectedStudentIds) {



      state.currentLetterSelectedStudentIds = new Set();



    }



    if (isChecked) {



      state.currentLetterSelectedStudentIds.add(studentId);



    } else {



      state.currentLetterSelectedStudentIds.delete(studentId);



    }



    this.updateLetterSelectedCount();



  },







  updateLetterSelectedCount() {



    const totalSelected = state.currentLetterSelectedStudentIds ? state.currentLetterSelectedStudentIds.size : 0;



    const countBadge = document.getElementById("letter-selected-count");



    if (countBadge) {



      countBadge.textContent = `${totalSelected} murid dipilih`;



      if (totalSelected > 0) {



        countBadge.className = "px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded-full font-mono";



      } else {



        countBadge.className = "px-2 py-0.5 bg-blue-100 text-blue-800 text-[10px] font-bold rounded-full font-mono";



      }



    }



  },







  selectAllLetterStudents(selectAll) {



    if (!state.currentLetterSelectedStudentIds) {



      state.currentLetterSelectedStudentIds = new Set();



    }



    



    // Get currently visible inputs in picker



    const visibleCheckboxes = document.querySelectorAll("input[name='letter-student-id']");



    visibleCheckboxes.forEach(cb => {



      cb.checked = selectAll;



      const sId = parseInt(cb.value);



      if (selectAll) {



        state.currentLetterSelectedStudentIds.add(sId);



      } else {



        state.currentLetterSelectedStudentIds.delete(sId);



      }



    });







    this.updateLetterSelectedCount();



  },







  async savePermissionLetter(e) {



    e.preventDefault();



    const id = document.getElementById("letter-form-id").value;



    const checked = Array.from(state.currentLetterSelectedStudentIds || []);







    if (checked.length === 0) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih sekurang-kurangnya seorang murid terlibat.' });



      return;



    }







    if (state.selectedLetterTeachers && state.selectedLetterTeachers.length > 3) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila pilih maksimum 3 orang cikgu sebagai guru pengiring.' });



      return;



    }







    const accompanying = (state.selectedLetterTeachers && state.selectedLetterTeachers.length > 0)



      ? state.selectedLetterTeachers.join(" & ")



      : (document.getElementById("let-form-teachers")?.value.trim() || state.currentUser?.full_name);







    const payload = {



      program_name: document.getElementById("let-form-program").value.trim(),



      destination_venue: document.getElementById("let-form-venue").value.trim(),



      start_datetime: document.getElementById("let-form-start").value.trim(),



      end_datetime: document.getElementById("let-form-end").value.trim(),



      organizer: document.getElementById("let-form-organizer").value.trim(),



      transportation: document.getElementById("let-form-transport").value.trim() || "Bas Sekolah",



      accompanying_teachers: accompanying,



      fee_amount: parseFloat(document.getElementById("let-form-fee").value) || 0.0,
      contact_phone: document.getElementById("let-form-phone").value.trim() || state.schoolSettings?.phone || "05-8391234",
      participation_level: document.getElementById("let-form-level")?.value || "Daerah",
      activity_category: document.getElementById("let-form-category")?.value || "Sukan & Permainan",
      represented_org_id: parseInt(document.getElementById("let-form-org")?.value) || null,
      student_ids: checked



    };







    try {



      let res;



      if (id) {



        res = await fetch(`/api/permission-letters/${id}`, {



          method: "PUT",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      } else {



        res = await fetch("/api/permission-letters", {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      }







      if (res.ok) {



        this.closeModal("modal-permission-letter");
        Swal.fire({ icon: 'success', title: 'Berjaya', text: id ? 'Surat kebenaran berjaya dikemas kini!' : `Surat kebenaran rasmi untuk ${checked.length} murid berjaya dijana!`, timer: 2000, showConfirmButton: false });
        this.loadPermissionLetters();
        this.loadExternalEvents();
        this.loadStudentPajskAchievements();



      } else {



        const err = await res.json();



        Swal.fire({ icon: 'error', title: 'Ralat', text: err.detail || 'Gagal menyimpan surat kebenaran.' });



      }



    } catch (err) {



      console.error(err);



    }



  },







  async deletePermissionLetter(letterId) {



    if (!this.canDelete()) {



      Swal.fire({



        icon: 'error',



        title: 'Akses Ditolak',



        text: 'Anda tidak mempunyai kebenaran untuk memadam surat kebenaran. Hanya akaun Admin, GPK Kokurikulum, Penyelaras, dan Setiausaha Sukan dibenarkan.',



        confirmButtonColor: '#1e3a8a'



      });



      return;



    }



    const res = await Swal.fire({



      title: 'Padam Surat Kebenaran?',



      text: 'Adakah anda pasti untuk memadam rekod surat kebenaran ini berserta senarai murid terlibat?',



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#e11d48',



      confirmButtonText: 'Ya, Padam',



      cancelButtonText: 'Batal'



    });







    if (res.isConfirmed) {



      try {



        const delRes = await fetch(`/api/permission-letters/${letterId}`, { method: "DELETE" });



        if (delRes.ok) {



          Swal.fire({ icon: 'success', title: 'Dipadam', text: 'Surat kebenaran berjaya dipadam!', timer: 1500, showConfirmButton: false });



          this.loadPermissionLetters();



        }



      } catch (err) {



        console.error(err);



      }



    }



  },







  async openConsentTracker(letterId) {



    try {



      const res = await fetch(`/api/permission-letters/${letterId}`);



      if (!res.ok) return;



      const letter = await res.json();







      let tableRows = letter.students.map((st, idx) => `



        <tr class="hover:bg-slate-50">



          <td class="p-2.5 text-center text-slate-500 font-bold">${idx + 1}</td>



          <td class="p-2.5 font-bold">${st.student_name} <span class="text-slate-500 font-normal">(${st.class_name})</span></td>



          <td class="p-2 text-center">



            <input type="text"



                   value="${st.jersey_no || ''}"



                   placeholder="-"



                   maxlength="5"



                   onchange="app.saveStudentJerseyNo(${letter.id}, ${st.student_id}, this.value)"



                   class="w-14 py-1 px-1.5 border border-slate-300 rounded-lg text-xs font-bold text-center outline-none focus:border-blue-500 font-mono"



                   title="Isi nombor jersi pemain">



          </td>



          <td class="p-2.5">${st.guardian_name || '-'} (${st.guardian_phone || '-'})</td>



          <td class="p-2.5">



            <select onchange="app.updateConsentStatus(${letter.id}, ${st.student_id}, this.value)" class="py-1 px-2 border rounded-lg text-xs font-bold ${this.getStatusBadgeClass(st.permission_status)}">



              <option value="Belum Diedarkan" ${st.permission_status === 'Belum Diedarkan' ? 'selected' : ''}>Belum Diedarkan</option>



              <option value="Diterima" ${st.permission_status === 'Diterima' ? 'selected' : ''}>Diterima (Menunggu)</option>



              <option value="Dibenarkan" ${st.permission_status === 'Dibenarkan' ? 'selected' : ''}>Dibenarkan Ibu Bapa</option>



              <option value="Tidak Dibenarkan" ${st.permission_status === 'Tidak Dibenarkan' ? 'selected' : ''}>Tidak Dibenarkan</option>



            </select>



          </td>



        </tr>



      `).join("");







      Swal.fire({



        title: `Akuan Penjaga & No. Jersi: ${letter.program_name}`,



        html: `



          <div class="text-left text-xs max-h-96 overflow-y-auto mt-3 border border-slate-200 rounded-xl">



            <table class="w-full">



              <thead class="bg-slate-100 font-bold sticky top-0">



                <tr><th class="p-2 text-center">Bil</th><th class="p-2">Murid</th><th class="p-2 text-center">No. Jersi</th><th class="p-2">Penjaga</th><th class="p-2">Status Kebenaran</th></tr>



              </thead>



              <tbody class="divide-y divide-slate-200">${tableRows}</tbody>



            </table>



          </div>



        `,



        width: '800px',



        showConfirmButton: false,



        showCloseButton: true



      });



    } catch (e) {



      console.error(e);



    }



  },







  async updateConsentStatus(letterId, studentId, status) {



    try {



      await fetch(`/api/permission-letters/${letterId}/students/${studentId}`, {



        method: "PUT",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({ permission_status: status })



      });



      this.loadPermissionLetters();



    } catch (e) {



      console.error(e);



    }



  },







  async openLetterPrintOptionsModal(letterId) {



    try {



      const res = await fetch(`/api/permission-letters/${letterId}`);



      if (!res.ok) return;



      const letter = await res.json();



      state.currentLetterToPrint = letter;







      document.getElementById("print-opt-letter-id").value = letter.id;



      document.getElementById("print-opt-letter-title").textContent = letter.program_name;



      document.getElementById("print-opt-letter-meta").textContent = `${letter.destination_venue} • ${letter.start_datetime} hingga ${letter.end_datetime}`;







      // Populate student selector



      const studentSelect = document.getElementById("print-opt-student-id");



      studentSelect.innerHTML = `<option value="all">🖨️ Cetak Semua Murid Terlibat (${letter.students.length} orang - 1 helaian bagi setiap murid)</option>` +



        letter.students.map((st, i) => `<option value="${st.student_id}">👤 Murid ${i + 1}: ${st.student_name} (${st.class_name}) - Cetak Individu (1 Muka Surat)</option>`).join("");







      document.getElementById("modal-letter-print-options").classList.remove("hidden");



      lucide.createIcons();



    } catch (e) {



      console.error(e);



    }



  },







  toggleLetterStudentFilter(format) {



    const container = document.getElementById("print-opt-student-filter-container");



    if (!container) return;



    if (format === "ro2") {



      container.classList.add("hidden");



    } else {



      container.classList.remove("hidden");



    }



  },







  executePrintSelectedFormat() {



    const letter = state.currentLetterToPrint;



    if (!letter) return;







    const format = document.querySelector("input[name='letter_print_format']:checked")?.value || "ro1";



    const studentScope = document.getElementById("print-opt-student-id")?.value || "all";







    this.closeModal("modal-letter-print-options");



    this.renderPermissionLetterPrintDocument(letter, format, studentScope);







    // Open print preview modal



    document.getElementById("modal-print-preview").classList.remove("hidden");



    lucide.createIcons();



  },







  
    renderParentConsentLandscapeSheet(st, letter, school) {
    const schoolName = (school && school.school_name) ? school.school_name : "SK SUNGAI DENDANG";
    const schoolAddress = (school && school.address) ? school.address : "34130 SELAMA, PERAK DR.";

    let addrLine1 = "34130 SELAMA";
    let addrLine2 = "PERAK DR.";
    if (schoolAddress.includes(",")) {
      const parts = schoolAddress.split(",");
      addrLine1 = parts[0].trim();
      addrLine2 = parts.slice(1).join(", ").trim();
    } else {
      addrLine1 = schoolAddress;
    }

    const schoolEmail = (school && school.email) ? school.email : "ABA6038@1bestarinet.yes.my";

    const programName = (letter.program_name || "-").toUpperCase();
    const destination = (letter.destination_venue || "-").toUpperCase();

    const malayMonths = ["JANUARI", "FEBRUARI", "MAC", "APRIL", "MEI", "JUN", "JULAI", "OGOS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DISEMBER"];
    const malayDays = ["AHAD", "ISNIN", "SELASA", "RABU", "KHAMIS", "JUMAAT", "SABTU"];

    let tarikhProgram = "-";
    let masaHariProgram = "-";
    const now = new Date();
    const tarikhSurat = `${now.getDate()}.${String(now.getMonth() + 1).padStart(2, '0')}.${now.getFullYear()}`;

    if (letter.start_datetime) {
      try {
        const d1 = new Date(letter.start_datetime.replace(" ", "T"));
        if (!isNaN(d1.getTime())) {
          const dayName = malayDays[d1.getDay()];
          const d1Str = `${d1.getDate()} ${malayMonths[d1.getMonth()]} ${d1.getFullYear()}`;
          let d2Str = "";
          if (letter.end_datetime) {
            const d2 = new Date(letter.end_datetime.replace(" ", "T"));
            if (!isNaN(d2.getTime()) && d1.toDateString() !== d2.toDateString()) {
              d2Str = ` HINGGA ${d2.getDate()} ${malayMonths[d2.getMonth()]} ${d2.getFullYear()}`;
            }
          }
          tarikhProgram = d1Str + d2Str;

          const t1 = letter.start_datetime.includes(" ") ? letter.start_datetime.split(" ")[1] : "";
          const t2 = (letter.end_datetime && letter.end_datetime.includes(" ")) ? letter.end_datetime.split(" ")[1] : "";
          if (t1 && t2) {
            masaHariProgram = `${dayName} ${t1} - ${t2}`;
          } else if (t1) {
            masaHariProgram = `${dayName} ${t1}`;
          } else {
            masaHariProgram = dayName;
          }
        }
      } catch(e) {
        tarikhProgram = letter.start_datetime;
      }
    }

    const studentNameDisplay = st && st.student_name 
      ? `<span style="font-weight: bold; text-decoration: underline;">${st.student_name}</span>`
      : `__________________________________`;
    
    const classNameDisplay = st && st.class_name
      ? `<span style="font-weight: bold; text-decoration: underline;">${st.class_name}</span>`
      : `_________`;

    const guardianNameDisplay = st && st.guardian_name
      ? `<span style="font-weight: bold; text-decoration: underline;">${st.guardian_name.toUpperCase()}</span>`
      : `___________________________________________________`;

    const icNumberDisplay = st && st.ic_number
      ? `<span style="font-weight: bold; text-decoration: underline;">${st.ic_number}</span>`
      : `______________________`;

    const addressDisplay = st && st.address
      ? `<span style="text-decoration: underline;">${st.address}</span>`
      : `____________________________________________`;

    const phoneDisplay = st && st.guardian_phone
      ? `<span style="font-weight: bold; text-decoration: underline;">${st.guardian_phone}</span>`
      : `_____________`;

    return `
      <div class="landscape-sheet letter-parent-sheet bg-white text-black p-0 rounded-none shadow-2xl border-0 w-full max-w-[1100px] mb-8 print:w-full print:max-w-none print:m-0 print:p-0 print:border-none print:shadow-none" style="page-break-after: always !important; break-after: page !important; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
        <div style="border: 1.5px solid #000; display: grid; grid-template-columns: 1fr 1fr; box-sizing: border-box; min-height: 182mm;">
          
          <!-- SEBELAH KIRI: SURAT MAKLUMAN SEKOLAH -->
          <div style="padding: 16px 20px; border-right: 1.5px solid #000; display: flex; flex-direction: column; box-sizing: border-box;">
            <div>
              <!-- Header Surat Makluman -->
              <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <img src="/static/images/school_logo.png?v=3" style="width: 52px; height: 52px; object-fit: contain;" alt="Logo SK Sungai Dendang">
                  <div style="font-size: 10pt; font-weight: bold; line-height: 1.25; text-transform: uppercase;">
                    <div>SK SUNGAI DENDANG</div>
                    <div>34130 SELAMA</div>
                    <div>PERAK DR.</div>
                  </div>
                </div>
                <div style="text-align: right; font-size: 8.8pt; line-height: 1.35; padding-top: 2px;">
                  <div>Email : ${schoolEmail}</div>
                  <div style="font-weight: 500; margin-top: 2px;">Tarikh : ${tarikhSurat}</div>
                </div>
              </div>

              <!-- Salutation -->
              <div style="font-size: 9.5pt; font-weight: bold; margin-bottom: 8px;">Tuan, puan,</div>

              <!-- Content paragraph 1 -->
              <div style="font-size: 9.2pt; text-align: justify; line-height: 1.45; margin-bottom: 14px;">
                Dengan sukacita dimaklumkan bahawa anak / jagaan tuan / puan yang bernama ${studentNameDisplay} dari kelas ${classNameDisplay} telah terpilih untuk mengikuti aktiviti / program tersebut pada ketentuan berikut :
              </div>

              <!-- Ketentuan Table -->
              <table style="width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 9pt;">
                <tr>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; width: 28%; text-align: left;">AKTIVITI</td>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: center;">${programName}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: left;">TARIKH</td>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: center;">${tarikhProgram}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: left;">MASA / HARI</td>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: center;">${masaHariProgram}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: left;">TEMPAT</td>
                  <td style="border: 1.5px solid #000; padding: 5px 8px; font-weight: bold; text-align: center;">${destination}</td>
                </tr>
              </table>

              <!-- Content paragraph 2 -->
              <div style="font-size: 9.2pt; text-align: justify; line-height: 1.45; margin-bottom: 14px;">
                2. &nbsp; Sehubungan dengan ini, pihak sekolah memohon tuan / puan melengkapkan borang kebenaran yang disertakan dan mengembalikannya dengan kadar yang segera.
              </div>
            </div>

            <!-- Sign-off Pengesahan Sekolah (Dikosongkan supaya GPK Ko / Guru Besar boleh cop & sign manual) -->
            <div style="margin-top: auto; font-size: 9.2pt; line-height: 1.45; padding-top: 14px;">
              <div>Sekian, Terima Kasih</div>
              <div style="font-weight: bold; margin: 4px 0;">“BERKHIDMAT UNTUK NEGARA”</div>
              <div>Saya yang menurut perintah,</div>
              <div style="margin-top: 50px;">
                <div style="border-bottom: 1px dotted #000; width: 220px;"></div>
                <div style="margin-top: 5px; font-size: 9.2pt;">( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )</div>
              </div>
            </div>
          </div>

          <!-- SEBELAH KANAN: SURAT KEBENARAN IBU BAPA -->
          <div style="padding: 16px 20px; display: flex; flex-direction: column; box-sizing: border-box;">
            <div>
              <!-- Centered Box Header -->
              <div style="text-align: center; margin-bottom: 12px;">
                <div style="display: inline-block; border: 1.5px solid #000; padding: 4px 28px; font-weight: bold; font-size: 11pt; letter-spacing: 0.5px;">
                  KEBENARAN IBU BAPA
                </div>
              </div>

              <!-- Parent Statement -->
              <div style="font-size: 8.8pt; text-align: justify; line-height: 1.42; margin-bottom: 12px;">
                Saya ${guardianNameDisplay} ibu bapa / penjaga membenarkan anak di bawah jagaan saya yang bernama ${studentNameDisplay} Sijil Beranak / K.P. bernombor ${icNumberDisplay} untuk menyertai aktiviti tersebut seperti ketentuan di bawah ini. :
              </div>

              <!-- Ketentuan Table (Identical) -->
              <table style="width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 8.8pt;">
                <tr>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; width: 28%; text-align: left;">AKTIVITI</td>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: center;">${programName}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: left;">TARIKH</td>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: center;">${tarikhProgram}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: left;">MASA / HARI</td>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: center;">${masaHariProgram}</td>
                </tr>
                <tr>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: left;">TEMPAT</td>
                  <td style="border: 1.5px solid #000; padding: 4.5px 8px; font-weight: bold; text-align: center;">${destination}</td>
                </tr>
              </table>

              <!-- Clauses 2, 3, 4 -->
              <div style="font-size: 8.2pt; text-align: justify; line-height: 1.35;">
                <div style="margin-bottom: 4px;">
                  2. &nbsp; Sehubungan dengan ini, saya ingin memaklumkan bahawa anak / jagaan saya adalah sihat, tiada masalah kesihatan dan boleh mengambil bahagian dalam aktiviti berkenaan. Saya juga mengakui bahawa anak saya dilindungi oleh Insuran Takaful.
                </div>
                <div style="margin-bottom: 4px;">
                  3. &nbsp; Saya faham bahawa pihak sekolah dan penganjur akan memastikan segala langkah keselamatan yang perlu. Walau bagaimana pun, saya mengakui tidak akan mengambil sebarang tindakan mahkamah terhadap pihak penganjur atau guru pengiring / sekolah jika berlaku sebarang kemalangan, kematian, kecacatan anggota, kehilangan anggota atau sebarang kecederaan lain terhadap anak / jagaan saya sama ada didalam perjalanan pergi dan balik mahu pun sepanjang aktiviti tersebut.
                </div>
                <div style="margin-bottom: 4px;">
                  4. &nbsp; Sehubungan dengan itu, saya juga membenarkan pihak sekolah dan penganjur untuk memberi sebarang rawatan yang perlu kepada anak / jagaan saya sekiranya didapati perlu oleh pihak yang berkenaan.
                </div>
              </div>

              <div style="font-size: 8.5pt; margin-top: 4px; margin-bottom: 6px;">Sekian, terima kasih.</div>
            </div>

            <!-- Parent Sign details -->
            <div style="margin-top: auto; font-size: 8.4pt; line-height: 1.55; padding-top: 6px;">
              <table style="width: 100%; border-collapse: collapse; border: none;">
                <tr style="border: none;">
                  <td style="border: none; padding: 2px 0; width: 44%;">Tandatangan ibu bapa / penjaga</td>
                  <td style="border: none; padding: 2px 0; width: 4%;">:</td>
                  <td style="border: none; padding: 2px 0; width: 52%;">_________________________</td>
                </tr>
                <tr style="border: none;">
                  <td style="border: none; padding: 2px 0;">Nombor Kad Pengenalan</td>
                  <td style="border: none; padding: 2px 0;">:</td>
                  <td style="border: none; padding: 2px 0;">_________________________</td>
                </tr>
                <tr style="border: none;">
                  <td style="border: none; padding: 2px 0;">Tarikh</td>
                  <td style="border: none; padding: 2px 0;">:</td>
                  <td style="border: none; padding: 2px 0;">_________________________</td>
                </tr>
                <tr style="border: none;">
                  <td style="border: none; padding: 2px 0; vertical-align: top;">Alamat Rumah</td>
                  <td style="border: none; padding: 2px 0; vertical-align: top;">:</td>
                  <td style="border: none; padding: 2px 0;">
                    ${addressDisplay}
                    ${st && st.address ? '' : '<br>____________________________________________'}
                  </td>
                </tr>
                <tr style="border: none;">
                  <td style="border: none; padding: 2px 0;">No. Telefon (Rumah)</td>
                  <td style="border: none; padding: 2px 0;">:</td>
                  <td style="border: none; padding: 2px 0;">
                    ____________________ &nbsp; Tel. Bimbit : ${phoneDisplay}
                  </td>
                </tr>
              </table>
            </div>

          </div>

        </div>
      </div>
    `;
  },

  renderParentConsentDocxSlip(st, letter, school, isCopy = false) {
    return this.renderParentConsentLandscapeSheet(st, letter, school);
  },

  renderPermissionLetterPrintDocument(letter, format, studentScope) {



    const doc = document.getElementById("print-document-container");
    if (doc) {
      if (format === "health" || format === "r02") {
        doc.classList.remove("max-w-4xl");
        doc.classList.add("max-w-6xl");
      } else {
        doc.classList.remove("max-w-6xl");
        doc.classList.add("max-w-4xl");
      }
    }



    const school = letter.school || state.schoolSettings;



    const now = new Date().toLocaleDateString("ms-MY", { day: "numeric", month: "long", year: "numeric" });







    let studentsToPrint = letter.students || [];



    if (studentScope && studentScope !== "all") {



      studentsToPrint = studentsToPrint.filter(st => String(st.student_id) === String(studentScope));



    }







    let html = "";







    // FORMAT 1: BORANG RO1 (INDIVIDU - FORMAT RASMI MSSM / KPM)



    if (format === "ro1") {



      if (studentsToPrint.length === 0) {



        html = `<div class="p-8 text-center text-slate-500 bg-white border border-slate-300 rounded-xl my-4 shadow">Tiada murid dipilih untuk cetakan Borang R01.</div>`;



      } else {



        html = `



          <div class="w-full flex flex-col items-center print:block print:w-full">



            ${studentsToPrint.map((st, idx) => {



              // Determine age group (Kumpulan Umur)



              let ageGroup = "12 TAHUN DAN KE BAWAH (B12)";



              if (st.class_name && (st.class_name.includes("1") || st.class_name.includes("2") || st.class_name.includes("3") || st.class_name.includes("4"))) {



                ageGroup = "10 / 12 TAHUN DAN KE BAWAH (B12)";



              }







              return `



              ${idx > 0 ? `



                <div class="no-print my-6 flex items-center justify-center w-full max-w-3xl">



                  <div class="h-px bg-slate-400 flex-1"></div>



                  <span class="mx-4 px-4 py-1.5 bg-slate-800 text-white rounded-full text-xs font-bold shadow-md flex items-center space-x-1.5">



                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-blue-400"></i>



                    <span>Helaian Baru / Muka Surat ${idx + 1}: ${st.student_name}</span>



                  </span>



                  <div class="h-px bg-slate-400 flex-1"></div>



                </div>



              ` : ''}







              <div class="r01-sheet bg-white text-black p-6 sm:p-9 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl mb-8 print:w-full print:max-w-none print:m-0 print:p-0 print:border-none print:shadow-none print:rounded-none" style="page-break-inside: avoid !important; page-break-after: always !important; break-after: page !important; min-height: 860px; display: block; box-sizing: border-box; width: 100%;">







                <div style="width: 100%;">



                  <!-- 1. HEADER BOX (TABLE WITH 2PX BLACK BORDER) -->



                  <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 4px; background-color: #ffffff;">



                    <tr>



                      <td style="padding: 6px 10px; vertical-align: middle; border: none;">



                        <div style="font-weight: bold; font-size: 11pt; text-transform: uppercase; margin-bottom: 4px; color: #000; letter-spacing: 0.5px;">BORANG PENDAFTARAN INDIVIDU</div>



                        <table style="width: 100%; font-size: 9pt; border-collapse: collapse; border: none; line-height: 1.4;">



                          <tr>



                            <td style="width: 90px; font-weight: bold; padding: 1.5px 0; border: none; color: #000;">PERMAINAN</td>



                            <td style="width: 10px; font-weight: bold; padding: 1.5px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; text-transform: uppercase; padding: 1.5px 0; border: none; color: #000;">${letter.program_name || 'MERENTAS DESA'}</td>



                          </tr>



                          <tr>



                            <td style="font-weight: bold; padding: 1.5px 0; border: none; color: #000;">NEGERI</td>



                            <td style="font-weight: bold; padding: 1.5px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; text-transform: uppercase; padding: 1.5px 0; border: none; color: #000;">PERAK DARUL RIDZUAN</td>



                          </tr>



                          <tr>



                            <td style="font-weight: bold; padding: 1.5px 0; border: none; color: #000;">JANTINA</td>



                            <td style="font-weight: bold; padding: 1.5px 0; border: none; color: #000;">:</td>



                            <td style="padding: 1.5px 0; border: none; color: #000;">



                              <span style="font-weight: bold; text-transform: uppercase;">${st.gender ? st.gender.toUpperCase() : 'LELAKI'}</span>



                              <span style="display: inline-block; width: 30px;"></span>



                              <span style="font-weight: bold;">KUMPULAN UMUR</span>



                              <span style="font-weight: bold;"> : </span>



                              <span style="font-weight: bold; text-transform: uppercase;">${ageGroup}</span>



                            </td>



                          </tr>



                        </table>



                      </td>



                      <td style="width: 68px; text-align: center; vertical-align: middle; padding: 2px; border: none;">



                        <img src="/static/images/mssm_logo.png" alt="MSSM Logo" style="height: 56px; width: auto; display: inline-block; object-fit: contain;">



                      </td>



                      <td style="width: 68px; text-align: center; vertical-align: middle; padding: 2px; border: none;">



                        <img src="${school.logo_url || '/static/images/school_logo.png'}" alt="Logo Sekolah" style="height: 56px; width: auto; display: inline-block; object-fit: contain;">



                      </td>



                      <td style="width: 85px; text-align: center; vertical-align: middle; padding: 4px 8px; border: none;">



                        <div style="border: 2px solid #000000; font-weight: 900; font-size: 24pt; padding: 4px 0; background: #ffffff; line-height: 1; color: #000;">



                          R01



                        </div>



                      </td>



                    </tr>



                  </table>







                  <!-- 2. MAKLUMAT PEMAIN & GAMBAR PASPORT (TABLE WITH 2PX BLACK BORDER) -->



                  <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 4px; background-color: #ffffff;">



                    <tr>



                      <!-- Left Info Table -->



                      <td style="padding: 6px 10px; vertical-align: top; border: none;">



                        <table style="width: 100%; font-size: 9pt; border-collapse: collapse; border: none; line-height: 1.45;">



                          <tr>



                            <td style="width: 135px; font-weight: normal; padding: 2.5px 0; border: none; color: #000;">Nama Pemain</td>



                            <td style="width: 10px; padding: 2.5px 0; border: none; color: #000;">:</td>



                            <td colspan="3" style="font-weight: bold; text-transform: uppercase; padding: 2.5px 0; border: none; color: #000;">${st.student_name}</td>



                          </tr>



                          <tr>



                            <td style="vertical-align: top; padding: 2.5px 0; border: none; color: #000;">Alamat Pemain<br><span style="font-size: 7.5pt; color: #333;">(Alamat Rumah)</span></td>



                            <td style="vertical-align: top; padding: 2.5px 0; border: none; color: #000;">:</td>



                            <td colspan="3" style="vertical-align: top; padding: 2.5px 0; border: none; color: #000;">${st.address || 'SK Sungai Dendang, 34130 Kubu Gajah, Selama, Perak'}</td>



                          </tr>



                          <tr>



                            <td style="font-weight: normal; padding: 2.5px 0; border: none; color: #000;">No.Kad Pengenalan</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; font-family: monospace; font-size: 9pt; padding: 2.5px 0; border: none; color: #000;">${st.ic_number || '........................'}</td>



                            <td style="width: 115px; font-weight: normal; padding: 2.5px 0; border: none; color: #000;">No. Telefon (Rumah):</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">${st.guardian_phone || '........................'}</td>



                          </tr>



                          <tr>



                            <td style="font-weight: normal; padding: 2.5px 0; border: none; color: #000;">Tingkatan / Tahun</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; padding: 2.5px 0; border: none; color: #000;">${st.class_name || '........................'}</td>



                            <td colspan="2" style="font-weight: normal; padding: 2.5px 0; border: none; color: #000;">Tarikh Daftar / Daftar Semula Ke Sekolah: 01/01/2026</td>



                          </tr>



                          <tr>



                            <td style="font-weight: normal; padding: 2.5px 0; border: none; color: #000;">No. Daftar Sekolah</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">:</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">........................</td>



                            <td style="font-weight: normal; padding: 2.5px 0; border: none; color: #000;">Angka Giliran UPSR :</td>



                            <td style="padding: 2.5px 0; border: none; color: #000;">........................</td>



                          </tr>



                        </table>



                      </td>







                      <!-- Right Passport Photo Box -->



                      <td style="width: 140px; border-left: 2px solid #000000 !important; vertical-align: middle; text-align: center; padding: 8px; background-color: #fafafa;">



                        <div style="border: 1.5px dashed #000000; height: 125px; display: flex; flex-direction: column; justify-content: space-around; padding: 6px 4px; font-size: 8pt; line-height: 1.3; background-color: #ffffff;">



                          <div>



                            <strong style="color: #000; font-size: 8pt;">Sediakan 2 keping</strong><br>



                            <span style="color: #000; font-size: 7.5pt;">Gambar ukuran Pasport</span>



                          </div>



                          <div style="font-size: 7.5pt; color: #333; border-top: 1px solid #ccc; padding-top: 4px;">



                            1 keping lekatkan disini



                          </div>



                        </div>



                      </td>



                    </tr>



                  </table>







                  <!-- 3. AKUAN KEBENARAN IBUBAPA / PENJAGA (TABLE WITH 2PX BLACK BORDER) -->



                  <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 4px; background-color: #ffffff;">



                    <!-- Title Bar -->



                    <tr style="border-bottom: 2px solid #000000 !important; background-color: #f1f5f9;">



                      <td colspan="5" style="font-weight: bold; text-align: center; text-transform: uppercase; font-size: 9pt; padding: 3.5px 4px; letter-spacing: 0.5px; color: #000; border: none;">



                        AKUAN KEBENARAN IBUBAPA / PENJAGA



                      </td>



                    </tr>



                    <tr>



                      <td style="padding: 6px 10px; border: none;" colspan="5">



                        <table style="width: 100%; font-size: 8.8pt; border-collapse: collapse; border: none; margin-bottom: 4px; line-height: 1.4;">



                          <tr>



                            <td style="width: 140px; padding: 2px 0; border: none; color: #000;">Nama Ibubapa / Penjaga</td>



                            <td style="width: 10px; padding: 2px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; text-transform: uppercase; padding: 2px 0; border: none; color: #000;">${st.guardian_name || '..........................................................'}</td>



                            <td style="width: 60px; padding: 2px 0; border: none; color: #000;">No. KP:</td>



                            <td style="width: 145px; padding: 2px 0; border: none; color: #000;">....................................</td>



                          </tr>



                          <tr>



                            <td style="padding: 2px 0; border: none; color: #000;">No. Telefon (Pejabat)</td>



                            <td style="padding: 2px 0; border: none; color: #000;">:</td>



                            <td style="padding: 2px 0; border: none; color: #000;">..........................................................</td>



                            <td style="padding: 2px 0; border: none; color: #000;">No. Tel Bimbit:</td>



                            <td style="font-weight: bold; font-family: monospace; padding: 2px 0; border: none; color: #000;">${st.guardian_phone || '....................................'}</td>



                          </tr>



                        </table>







                        <p style="text-align: justify; font-size: 8.2pt; line-height: 1.35; margin: 4px 0; color: #000;">



                          Saya bapa / penjaga kepada pelajar di atas mengesahkan segala keterangan di atas adalah benar dan gambar terbaru adalah betul. 



                          Saya juga membenarkan anak / jagaan saya didaftarkan sebagai pemain <strong style="text-decoration: underline; text-transform: uppercase;">${letter.program_name || 'MERENTAS DESA'}</strong> untuk pasukan <strong style="text-decoration: underline; text-transform: uppercase;">${school.school_name || 'SK SUNGAI DENDANG'} / PERAK</strong> dan bersetuju mematuhi Perlembagaan, undang-undang, peraturan-peraturan, Pekeliling-pekeliling dan syarat-syarat mengenai pertandingan ini. Saya juga faham bahawa pihak tuan sentiasa memberikan segala penerangan dan akan mengambil langkah-langkah keselamatan dan pengawasan yang diperlukan sepanjang masa kejohanan tersebut.



                        </p>







                        <table style="width: 100%; font-size: 8.8pt; border-collapse: collapse; border: none; margin-top: 8px;">



                          <tr>



                            <td style="width: 55%; padding: 0; border: none; color: #000;">Tandatangan : ___________________________________</td>



                            <td style="width: 45%; padding: 0; border: none; color: #000;">Tarikh : ___________________________</td>



                          </tr>



                        </table>



                      </td>



                    </tr>



                  </table>







                  <!-- 4. AKUAN PENGETUA / GURU PENOLONG KANAN (TABLE WITH 2PX BLACK BORDER) -->



                  <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 4px; background-color: #ffffff;">



                    <!-- Title Bar -->



                    <tr style="border-bottom: 2px solid #000000 !important; background-color: #f1f5f9;">



                      <td colspan="5" style="font-weight: bold; text-align: center; text-transform: uppercase; font-size: 9pt; padding: 3.5px 4px; letter-spacing: 0.5px; color: #000; border: none;">



                        AKUAN PENGETUA / GURU PENOLONG KANAN



                      </td>



                    </tr>



                    <tr>



                      <td style="padding: 6px 10px; border: none;" colspan="5">



                        <table style="width: 100%; font-size: 8.8pt; border-collapse: collapse; border: none; line-height: 1.4;">



                          <tr>



                            <td style="width: 200px; padding: 2px 0; border: none; color: #000;">Nama Pengetua / Guru Penolong Kanan</td>



                            <td style="width: 10px; padding: 2px 0; border: none; color: #000;">:</td>



                            <td style="font-weight: bold; text-transform: uppercase; padding: 2px 0; border: none; color: #000;">${school.principal_name || 'GURU BESAR SK SUNGAI DENDANG'}</td>



                            <td style="width: 110px; padding: 2px 0; border: none; color: #000;">No. Telefon Sekolah :</td>



                            <td style="width: 90px; padding: 2px 0; border: none; color: #000;">${school.phone || '05-8391234'}</td>



                          </tr>



                          <tr>



                            <td style="vertical-align: top; padding: 2px 0; border: none; color: #000;">Alamat Sekolah</td>



                            <td style="vertical-align: top; padding: 2px 0; border: none; color: #000;">:</td>



                            <td colspan="3" style="padding: 2px 0; border: none; color: #000;">${school.address || 'SK Sungai Dendang, 34130 Kubu Gajah, Selama, Perak Darul Ridzuan'}</td>



                          </tr>



                        </table>







                        <p style="font-size: 8.2pt; margin: 4px 0; color: #000;">



                          Saya mengesahkan segala keterangan di atas adalah betul dan gambar di atas adalah terbaru dan benar



                        </p>







                        <table style="width: 100%; font-size: 8.8pt; border-collapse: collapse; border: none; margin-top: 8px;">



                          <tr>



                            <td style="width: 60%; vertical-align: top; padding: 0; border: none; color: #000;">



                              <div>___________________________________</div>



                              <div style="font-size: 7.5pt; color: #222; margin-top: 1px;">(Tandatangan dan Cop Rasmi)</div>



                              <div style="margin-top: 3px;">Nama : ${school.principal_name || '..........................................................'}</div>



                              <div style="margin-top: 2px;">No. KP : ..........................................................</div>



                            </td>



                            <td style="width: 40%; vertical-align: top; text-align: left; padding: 0; border: none; color: #000;">



                              <div>Tarikh : ___________________________</div>



                            </td>



                          </tr>



                        </table>



                      </td>



                    </tr>



                  </table>







                  <!-- 5. AKUAN PENGURUS PASUKAN DAN SETIAUSAHA AGUNG MSSM NEGERI / KETUA UNIT SUKAN JPN -->



                  <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 0px; background-color: #ffffff;">



                    <!-- Title Bar -->



                    <tr style="border-bottom: 2px solid #000000 !important; background-color: #f1f5f9;">



                      <td colspan="2" style="font-weight: bold; text-align: center; text-transform: uppercase; font-size: 8.5pt; padding: 3.5px 4px; letter-spacing: 0.5px; color: #000; border: none;">



                        AKUAN PENGURUS PASUKAN DAN SETIAUSAHA AGUNG MSSM NEGERI / KETUA UNIT SUKAN JPN



                      </td>



                    </tr>



                    <tr>



                      <td colspan="2" style="padding: 6px 10px; border: none;">



                        <p style="text-align: center; font-size: 8.2pt; line-height: 1.35; margin: 2px 0 6px 0; color: #000;">



                          Diakui penama di atas adalah ahli pasukan ini yang menyertai Kejohanan / Pertandingan Majlis Sukan Sekolah-sekolah Malaysia<br>



                          Dan sepanjang pengetahuan saya semua maklumat yang diberi adalah benar.



                        </p>







                        <table style="width: 100%; font-size: 8.2pt; border-collapse: collapse; border: none; margin-top: 8px;">



                          <tr>



                            <!-- Left Column: Pengurus Pasukan -->



                            <td style="width: 50%; vertical-align: top; padding-right: 15px; border: none; color: #000;">



                              <div>_____________________________________</div>



                              <div style="font-weight: bold; text-align: center; width: 190px; margin-top: 2px;">Pengurus Pasukan</div>



                              <div style="margin-top: 4px;">Nama : ................................................</div>



                              <div style="margin-top: 1px;">No. KP : ................................................</div>



                              <div style="margin-top: 1px;">Jawatan : Guru Pengiring / Pengurus Pasukan</div>



                              <div style="margin-top: 1px;">Tarikh : ................................................</div>



                            </td>







                            <!-- Right Column: Setiausaha Agung MSSM Negeri -->



                            <td style="width: 50%; vertical-align: top; padding-left: 10px; border: none; color: #000;">



                              <div>_____________________________________</div>



                              <div style="font-weight: bold; font-size: 7.8pt; width: 230px; margin-top: 2px;">Setiausaha Agung MSSM Negeri / Ketua Unit Sukan Negeri</div>



                              <div style="margin-top: 4px;">Cop Rasmi :</div>



                              <div style="height: 18px;"></div>



                              <div>Tarikh : ................................................</div>



                            </td>



                          </tr>



                        </table>



                      </td>



                    </tr>



                  </table>



                </div>







              </div>



              `;



            }).join("")}



          </div>



        `;



      }



    }







    // FORMAT 2: BORANG RO2 (BORANG PENDAFTARAN PASUKAN MSSM - FORMAT RASMI 16 MURID 1 PAGE)



    else if (format === "ro2") {



      // Determine Gender and Age Group



      let genderStr = "LELAKI / PEREMPUAN";



      if (letter.students && letter.students.length > 0) {



        const genders = new Set(letter.students.map(s => (s.gender || '').toUpperCase()));



        if (genders.size === 1) {



          genderStr = Array.from(genders)[0];



        } else if (genders.has("LELAKI") && genders.has("PEREMPUAN")) {



          genderStr = "LELAKI & PEREMPUAN";



        }



      }







      let ageGroup = "12 TAHUN DAN KE BAWAH (B12)";



      if (letter.students && letter.students.some(st => st.class_name && (st.class_name.includes("1") || st.class_name.includes("2") || st.class_name.includes("3") || st.class_name.includes("4")))) {



        ageGroup = "10 / 12 TAHUN DAN KE BAWAH (B12)";



      }







      // Parse Accompanying Teachers



      let rawTeachers = (letter.accompanying_teachers || '').split(/[&,;]|\bdan\b/i).map(t => t.trim()).filter(Boolean);



      if (rawTeachers.length === 0 && state.currentUser?.full_name) {



        rawTeachers = [state.currentUser.full_name];



      }







      const officers = [];



      for (let i = 0; i < 6; i++) {



        if (rawTeachers[i]) {



          let role = i === 0 ? "Pengurus Pasukan" : (i === 1 ? "Jurulatih" : "Guru Pengiring");



          officers.push({ name: rawTeachers[i], role: role, school: school.school_name || "SK SUNGAI DENDANG" });



        } else {



          officers.push({ name: "", role: "", school: "" });



        }



      }







      // 16 Fixed Player Rows



      const maxPlayers = 16;



      const players = [];



      const enrolledStudents = letter.students || [];



      for (let i = 0; i < maxPlayers; i++) {



        if (enrolledStudents[i]) {



          players.push({



            student_id: enrolledStudents[i].student_id,



            name: enrolledStudents[i].student_name,



            ic: enrolledStudents[i].ic_number || "-",



            jersey_no: enrolledStudents[i].jersey_no || "",



            school: school.school_name || "SK SUNGAI DENDANG"



          });



        } else {



          players.push({ student_id: null, name: "", ic: "", jersey_no: "", school: "" });



        }



      }







      const managerName = officers[0].name || (rawTeachers[0] || '................................................');







      html = `



        <div class="w-full flex flex-col items-center print:block print:w-full">



          <div class="r02-sheet r01-sheet bg-white text-black p-5 sm:p-8 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl mb-8 print:w-full print:max-w-none print:m-0 print:p-0 print:border-none print:shadow-none print:rounded-none" style="page-break-inside: avoid !important; page-break-after: always !important; break-after: page !important; font-family: Arial, Helvetica, sans-serif; font-size: 9pt; line-height: 1.25; color: #000000; box-sizing: border-box; background-color: #ffffff; width: 100%;">







            <!-- 1. HEADER BOX (TABLE WITH 2PX BLACK BORDER) -->



            <table style="width: 100%; border: 2px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 6px; background-color: #ffffff;">



              <tr>



                <td style="padding: 6px 10px; vertical-align: middle; border: none;">



                  <div style="font-weight: 800; font-size: 13pt; text-transform: uppercase; text-align: center; margin-bottom: 5px; color: #000; letter-spacing: 0.5px;">



                    BORANG PENDAFTARAN PASUKAN MSSM



                  </div>



                  <table style="width: 100%; font-size: 9.5pt; border-collapse: collapse; border: none; line-height: 1.4;">



                    <tr>



                      <td style="width: 80px; font-weight: bold; padding: 2px 0; border: none; color: #000;">SUKAN</td>



                      <td style="width: 12px; font-weight: bold; padding: 2px 0; border: none; color: #000;">:</td>



                      <td style="font-weight: bold; text-transform: uppercase; padding: 2px 0; border: none; color: #000; border-bottom: 1px solid #000;">${letter.program_name || 'MERENTAS DESA'}</td>



                    </tr>



                    <tr>



                      <td style="font-weight: bold; padding: 2px 0; border: none; color: #000;">NEGERI</td>



                      <td style="width: 12px; font-weight: bold; padding: 2px 0; border: none; color: #000;">:</td>



                      <td style="font-weight: bold; text-transform: uppercase; padding: 2px 0; border: none; color: #000; border-bottom: 1px solid #000;">PERAK DARUL RIDZUAN</td>



                    </tr>



                    <tr>



                      <td style="font-weight: bold; padding: 2px 0; border: none; color: #000;">JANTINA</td>



                      <td style="width: 12px; font-weight: bold; padding: 2px 0; border: none; color: #000;">:</td>



                      <td style="padding: 2px 0; border: none; color: #000;">



                        <span style="font-weight: bold; text-transform: uppercase; display: inline-block; min-width: 130px; border-bottom: 1px solid #000;">${genderStr}</span>



                        <span style="display: inline-block; width: 25px;"></span>



                        <span style="font-weight: bold;">KUMPULAN UMUR:</span>



                        <span style="font-weight: bold; text-transform: uppercase; display: inline-block; min-width: 180px; border-bottom: 1px solid #000; margin-left: 6px;">${ageGroup}</span>



                      </td>



                    </tr>



                  </table>



                </td>



                <td style="width: 75px; text-align: center; vertical-align: middle; padding: 4px; border: none;">



                  <img src="/static/images/mssm_logo.png" alt="MSSM Logo" style="height: 60px; width: auto; display: inline-block; object-fit: contain;">



                </td>



                <td style="width: 90px; text-align: center; vertical-align: middle; padding: 4px 8px; border-left: 2px solid #000000 !important;">



                  <div style="font-weight: 900; font-size: 26pt; background: #ffffff; line-height: 1; color: #000;">



                    R02



                  </div>



                </td>



              </tr>



            </table>







            <!-- 2. JADUAL PEGAWAI PASUKAN (6 ROWS) -->



            <table style="width: 100%; border: 1.5px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 6px; background-color: #ffffff; font-size: 9pt;">



              <thead>



                <tr style="background-color: #f1f5f9; border-bottom: 1.5px solid #000000; height: 26px;">



                  <th style="width: 36px; text-align: center; padding: 3px 4px; border: 1px solid #000000; font-weight: bold; color: #000;">Bil</th>



                  <th style="width: 44%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">Nama Pegawai</th>



                  <th style="width: 25%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">Jawatan</th>



                  <th style="width: 27%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">Sekolah</th>



                </tr>



              </thead>



              <tbody>



                ${officers.map((off, idx) => `



                  <tr style="height: 24px;">



                    <td style="text-align: center; font-weight: bold; padding: 2.5px 4px; border: 1px solid #000000; color: #000;">${idx + 1}</td>



                    <td style="padding: 2.5px 6px; border: 1px solid #000000; font-weight: ${off.name ? 'bold' : 'normal'}; text-transform: uppercase; color: #000;">${off.name || '&nbsp;'}</td>



                    <td style="text-align: center; padding: 2.5px 6px; border: 1px solid #000000; color: #000;">${off.role || '&nbsp;'}</td>



                    <td style="text-align: center; padding: 2.5px 6px; border: 1px solid #000000; text-transform: uppercase; font-size: 8.5pt; color: #000;">${off.school || '&nbsp;'}</td>



                  </tr>



                `).join("")}



              </tbody>



            </table>







            <!-- 3. JADUAL SENARAI PEMAIN (16 FIXED ROWS DENGAN NO. JERSI DI ANTARA NO. KP DAN SEKOLAH) -->



            <table style="width: 100%; border: 1.5px solid #000000 !important; border-collapse: collapse !important; margin-bottom: 6px; background-color: #ffffff; font-size: 9pt;">



              <thead>



                <tr style="background-color: #f1f5f9; border-bottom: 1.5px solid #000000; height: 26px;">



                  <th style="width: 32px; text-align: center; padding: 3px 2px; border: 1px solid #000000; font-weight: bold; color: #000;">Bil</th>



                  <th style="width: 42%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">Nama Pemain</th>



                  <th style="width: 24%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">No. Surat Beranak / No. KP</th>



                  <th style="width: 65px; text-align: center; padding: 3px 2px; border: 1px solid #000000; font-weight: bold; color: #000;">No. Jersi</th>



                  <th style="width: 24%; text-align: center; padding: 3px 6px; border: 1px solid #000000; font-weight: bold; color: #000;">Sekolah</th>



                </tr>



              </thead>



              <tbody>



                ${players.map((pl, idx) => `



                  <tr style="height: 23px;">



                    <td style="text-align: center; font-weight: bold; padding: 2px 2px; border: 1px solid #000000; color: #000;">${idx + 1}</td>



                    <td style="padding: 2px 6px; border: 1px solid #000000; font-weight: ${pl.name ? 'bold' : 'normal'}; text-transform: uppercase; color: #000;">${pl.name || '&nbsp;'}</td>



                    <td style="text-align: center; font-family: monospace; font-size: 9pt; padding: 2px 6px; border: 1px solid #000000; color: #000;">${pl.ic || '&nbsp;'}</td>



                    <td style="text-align: center; padding: 1px 2px; border: 1px solid #000000; font-weight: bold; color: #000;">



                      ${pl.name ? `



                        <input type="text"



                               value="${pl.jersey_no || ''}"



                               placeholder="-"



                               maxlength="5"



                               data-letter-id="${letter.id}"



                               data-student-id="${pl.student_id}"



                               oninput="app.onJerseyInputChange(this, ${letter.id}, ${pl.student_id})"



                               onchange="app.saveStudentJerseyNo(${letter.id}, ${pl.student_id}, this.value)"



                               class="jersey-input w-full text-center font-bold text-xs bg-transparent border-0 focus:ring-1 focus:ring-blue-500 rounded p-0 m-0 outline-none print:hidden no-print"



                               title="Klik untuk mengisi nombor jersi">



                        <span class="jersey-print-val hidden print:inline font-bold">${pl.jersey_no || '&nbsp;'}</span>



                      ` : '&nbsp;'}



                    </td>



                    <td style="text-align: center; padding: 2px 6px; border: 1px solid #000000; text-transform: uppercase; font-size: 8.5pt; color: #000;">${pl.school || '&nbsp;'}</td>



                  </tr>



                `).join("")}



              </tbody>



            </table>







            <!-- 4. PENGESAHAN & TANDATANGAN (STATEMENT & 2 COLUMNS) -->



            <div style="margin-top: 6px; padding-top: 2px;">



              <p style="font-weight: bold; font-size: 9pt; line-height: 1.35; margin: 0 0 10px 0; color: #000;">



                Mengesahkan bahawa segala maklumat yang dinyatakan di atas adalah benar seperti dalam borang R01.



              </p>







              <table style="width: 100%; font-size: 9pt; border-collapse: collapse; border: none; margin-top: 8px;">



                <tr>



                  <!-- Left Column: Pengurus Pasukan -->



                  <td style="width: 50%; vertical-align: top; padding-right: 25px; border: none; color: #000;">



                    <div style="border-bottom: 1px dotted #000; width: 260px; height: 36px; margin-bottom: 4px;"></div>



                    <div style="font-weight: bold; font-size: 9.5pt; margin-top: 2px; margin-bottom: 6px;">Pengurus Pasukan</div>



                    <table style="font-size: 9pt; border-collapse: collapse; border: none; width: 100%; line-height: 1.45;">



                      <tr><td style="width: 95px; padding: 2px 0; border: none;">Nama</td><td style="width: 12px; border: none;">:</td><td style="font-weight: bold; text-transform: uppercase; border: none;">${managerName}</td></tr>



                      <tr><td style="padding: 2px 0; border: none;">No. KP</td><td style="border: none;">:</td><td style="border: none;">................................................</td></tr>



                      <tr><td style="padding: 2px 0; border: none;">Tarikh</td><td style="border: none;">:</td><td style="border: none;">................................................</td></tr>



                      <tr><td style="padding: 2px 0; border: none;">No. Tel. Bimbit</td><td style="border: none;">:</td><td style="font-mono; border: none;">${school.phone || '................................................'}</td></tr>



                    </table>



                  </td>







                  <!-- Right Column: Pengesahan Guru Besar -->



                  <td style="width: 50%; vertical-align: top; padding-left: 20px; border: none; color: #000;">



                    <div style="border-bottom: 1px dotted #000; width: 260px; height: 36px; margin-bottom: 4px;"></div>



                    <div style="font-weight: bold; font-size: 9.5pt; margin-top: 2px; margin-bottom: 6px;">Guru Besar</div>



                    <table style="font-size: 9pt; border-collapse: collapse; border: none; width: 100%; line-height: 1.45;">



                      <tr><td style="width: 95px; padding: 2px 0; border: none;">Nama</td><td style="width: 12px; border: none;">:</td><td style="font-weight: bold; text-transform: uppercase; border: none;">${school.principal_name || '................................................'}</td></tr>



                      <tr><td style="padding: 2px 0; border: none;">Cop Rasmi</td><td style="border: none;">:</td><td style="border: none;"></td></tr>



                      <tr><td style="padding: 2px 0; border: none;">Tarikh</td><td style="border: none;">:</td><td style="border: none;">................................................</td></tr>



                      <tr><td style="padding: 2px 0; border: none;">No. Tel. Bimbit</td><td style="border: none;">:</td><td style="border: none;">${school.phone || '................................................'}</td></tr>



                    </table>



                  </td>



                </tr>



              </table>



            </div>







          </div>



        </div>



      `;



    }







    // FORMAT 3: KEBENARAN WARIS & AKUAN KESIHATAN



    else if (format === "health") {
      if (studentsToPrint.length === 0) {
        html = `<div class="p-8 text-center text-slate-500 bg-white border border-slate-300 rounded-xl my-4 shadow">Tiada murid dipilih untuk cetakan Surat Kebenaran.</div>`;
      } else {
        html = `
          <div class="w-full flex flex-col items-center">
            ${studentsToPrint.map((st, sIdx) => `
              ${sIdx > 0 ? `
                <div class="no-print my-6 flex items-center justify-center w-full max-w-4xl">
                  <div class="h-px bg-slate-400 flex-1"></div>
                  <span class="mx-4 px-4 py-1.5 bg-slate-800 text-white rounded-full text-xs font-bold shadow-md flex items-center space-x-1.5">
                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-blue-400"></i>
                    <span>Helaian / Muka Surat ${sIdx + 1} (${st.student_name} - A4 Landscape)</span>
                  </span>
                  <div class="h-px bg-slate-400 flex-1"></div>
                </div>
              ` : ''}

              ${this.renderParentConsentLandscapeSheet(st, letter, school)}
            `).join("")}
          </div>
        `;
      }
    }

    doc.innerHTML = html;



    lucide.createIcons();



  },







  // ==========================================



  // VIEW 6: PENYERTAAN LUAR & PAJSK



  // ==========================================



  switchPajskTab(tabName) {



    state.pajskActiveTab = tabName;



    const tabEvents = document.getElementById("tab-pajsk-events");



    const tabStudents = document.getElementById("tab-pajsk-students");



    const contEvents = document.getElementById("pajsk-events-container");



    const contStudents = document.getElementById("pajsk-students-container");







    if (tabName === "students") {



      if (tabEvents) { tabEvents.classList.remove("active"); tabEvents.classList.add("text-slate-500"); }



      if (tabStudents) { tabStudents.classList.add("active"); tabStudents.classList.remove("text-slate-500"); }



      if (contEvents) contEvents.classList.add("hidden");



      if (contStudents) contStudents.classList.remove("hidden");



      this.loadStudentPajskAchievements();



    } else {



      if (tabStudents) { tabStudents.classList.remove("active"); tabStudents.classList.add("text-slate-500"); }



      if (tabEvents) { tabEvents.classList.add("active"); tabEvents.classList.remove("text-slate-500"); }



      if (contStudents) contStudents.classList.add("hidden");



      if (contEvents) contEvents.classList.remove("hidden");



      this.loadExternalEvents();



    }



  },







  // ==========================================



  // VIEW 7: KEJOHANAN SUKAN SEKOLAH (LENGKAP)



  // ==========================================



  switchSportsDaySubTab(tabName) {



    state.sportsActiveSubTab = tabName;



    const tabs = ["standings", "events", "enrollment", "lanes", "results"];



    tabs.forEach(t => {



      const btn = document.getElementById(`tab-sd-${t}`);



      const cont = document.getElementById(`sd-${t}-container`);



      if (btn) {



        if (t === tabName) {



          btn.classList.add("active");



          btn.classList.remove("text-slate-500");



        } else {



          btn.classList.remove("active");



          btn.classList.add("text-slate-500");



        }



      }



      if (cont) {



        if (t === tabName) cont.classList.remove("hidden");



        else cont.classList.add("hidden");



      }



    });







    if (tabName === "standings") this.loadSportsDayOverview();



    else if (tabName === "events") this.loadSportsDayEventsList();



    else if (tabName === "enrollment") this.loadSportsDayEnrollmentView();



    else if (tabName === "lanes") this.loadSportsDayLanesView();



    else if (tabName === "results") this.loadSportsDayResultsView();







    lucide.createIcons();



  },







  async loadSportsDayOverview() {



    try {



      const res = await fetch("/api/sports/overall-standings");



      if (!res.ok) return;



      const data = await res.json();



      state.sportsOverallData = data;







      // 1. Render House Tally Cards (Combined Sukan + Merentas Desa)



      const tallyContainer = document.getElementById("sports-day-house-tally");



      if (tallyContainer && data.house_summary) {



        tallyContainer.innerHTML = data.house_summary.map((h, idx) => `



          <div class="glass-card p-4 rounded-2xl border-l-4 shadow-sm relative overflow-hidden bg-white" style="border-left-color: ${h.color_code || '#cbd5e1'};">



            ${idx === 0 ? '<span class="absolute top-2 right-2 px-2.5 py-0.5 bg-yellow-400 text-yellow-950 text-[10px] font-black rounded-full uppercase tracking-wider shadow-xs animate-bounce">🏆 JUARA KESELURUHAN</span>' : ''}



            <div class="text-xs font-black text-navy-950 uppercase pr-16">${h.name}</div>



            <div class="mt-2 flex items-baseline justify-between">



              <div>



                <span class="text-2xl font-black" style="color: ${h.color_code || '#1e293b'};">${h.total_points}</span>



                <span class="text-[11px] font-bold text-slate-500 ml-1">Mata</span>



              </div>



              <div class="text-right text-[11px] font-bold space-x-1 text-slate-700">



                <span title="Emas">🥇 ${h.total_gold}</span>



                <span title="Perak">🥈 ${h.total_silver}</span>



                <span title="Gangsa">🥉 ${h.total_bronze}</span>



              </div>



            </div>



            <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500 font-semibold">



              <span>Sukan: <b class="text-slate-800">${h.sd_points}m</b></span>



              <span>Merentas Desa: <b class="text-slate-800">${h.cc_points}m</b></span>



              ${h.sd_broken_records > 0 ? `<span class="text-purple-700 font-bold">⚡ ${h.sd_broken_records} Rekod</span>` : ''}



            </div>



          </div>



        `).join("");



      }







      // 2. Render Breakdown Table



      const breakdownBody = document.getElementById("sd-breakdown-table-body");



      if (breakdownBody && data.house_summary) {



        breakdownBody.innerHTML = data.house_summary.map((h, idx) => `



          <tr class="hover:bg-slate-50 transition">



            <td class="p-3 font-black text-slate-600">${idx + 1}</td>



            <td class="p-3 text-left">



              <div class="flex items-center space-x-2">



                <span class="w-3 h-3 rounded-full inline-block" style="background-color: ${h.color_code || '#64748b'};"></span>



                <span class="font-bold text-navy-950">${h.name}</span>



                ${idx === 0 ? '<span class="text-[10px] px-1.5 py-0.2 bg-yellow-100 text-yellow-800 font-bold rounded">Juara</span>' : ''}



              </div>



            </td>



            <td class="p-3 text-blue-700">${h.sd_points}</td>



            <td class="p-3 text-emerald-700">${h.cc_points}</td>



            <td class="p-3 text-amber-600">🥇 ${h.total_gold}</td>



            <td class="p-3 text-slate-600">🥈 ${h.total_silver}</td>



            <td class="p-3 text-amber-800">🥉 ${h.total_bronze}</td>



            <td class="p-3 font-bold ${h.sd_broken_records > 0 ? 'text-purple-700' : 'text-slate-400'}">${h.sd_broken_records > 0 ? `⚡ ${h.sd_broken_records}` : '-'}</td>



            <td class="p-3 font-black text-sm text-navy-950" style="color: ${h.color_code || '#1e293b'};">${h.total_points}</td>



          </tr>



        `).join("");



      }







      // 3. Render Special Awards (Olahragawan / Olahragawati)



      const athletesContainer = document.getElementById("sd-athletes-container");



      if (athletesContainer) {



        const awards = [



          { title: "Olahragawan Sesi Semasa", sub: "Lelaki Terbaik (Tahap 2)", data: data.olahragawan, icon: "🏃‍♂️", color: "bg-blue-50 border-blue-200 text-blue-900" },



          { title: "Olahragawati Sesi Semasa", sub: "Perempuan Terbaik (Tahap 2)", data: data.olahragawati, icon: "🏃‍♀️", color: "bg-rose-50 border-rose-200 text-rose-900" },



          { title: "Olahragawan Harapan", sub: "Lelaki Terbaik (Tahap 1)", data: data.olahragawan_harapan, icon: "🌟", color: "bg-amber-50 border-amber-200 text-amber-900" },



          { title: "Olahragawati Harapan", sub: "Perempuan Terbaik (Tahap 1)", data: data.olahragawati_harapan, icon: "✨", color: "bg-purple-50 border-purple-200 text-purple-900" }



        ];







        athletesContainer.innerHTML = awards.map(a => {



          const d = a.data;



          return `



            <div class="glass-card p-4 rounded-2xl border shadow-sm ${a.color} flex flex-col justify-between">



              <div>



                <div class="flex items-center justify-between">



                  <span class="text-xl">${a.icon}</span>



                  <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-white/80 border">${a.title}</span>



                </div>



                <div class="text-[10px] font-bold text-slate-500 mt-1">${a.sub}</div>



                ${d ? `



                  <h4 class="font-black text-sm text-slate-900 mt-2 line-clamp-1" title="${d.full_name}">${d.full_name}</h4>



                  <div class="text-[11px] font-semibold text-slate-600 mt-0.5">



                    <span>${d.class_name}</span> • <span class="font-bold">${d.sport_house_name}</span>



                  </div>



                ` : `



                  <div class="text-xs text-slate-400 italic mt-3">Belum ditentukan (Menunggu keputusan acara)</div>



                `}



              </div>



              ${d ? `



                <div class="mt-3 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] font-bold text-slate-700">



                  <span>🥇 ${d.gold_count} Emas</span>



                  <span>⚡ ${d.broken_records_count || 0} Rekod</span>



                  <span class="text-navy-950">${d.total_points} Mata</span>



                </div>



              ` : ''}



            </div>



          `;



        }).join("");



      }







      lucide.createIcons();



    } catch (err) {



      console.error("Load sports overview error:", err);



    }



  },







  async loadSportsDayEventsList() {



    try {



      const res = await fetch("/api/sports/events");



      if (!res.ok) return;



      state.sportsEvents = await res.json();



      this.renderSportsEventsTable(state.sportsEvents);



    } catch (err) {



      console.error("Load sports events error:", err);



    }



  },







  renderSportsEventsTable(events) {



    const tbody = document.getElementById("sd-events-table-body");



    if (!tbody) return;







    if (!events || events.length === 0) {



      tbody.innerHTML = `<tr><td colspan="8" class="p-6 text-center text-slate-400">Tiada acara sukan dijumpai. Klik "Daftar Acara Sukan Baharu" untuk mula menambah acara.</td></tr>`;



      return;



    }







    tbody.innerHTML = events.map((ev, idx) => `



      <tr class="hover:bg-slate-50 transition">



        <td class="p-3.5 text-center font-bold text-slate-500">${idx + 1}</td>



        <td class="p-3.5">



          <div class="font-black text-navy-950">${ev.event_name}</div>



          <div class="text-[10px] text-slate-500 font-semibold">${ev.academic_year} • Tarikh: ${ev.event_date || '2026-07-15'}</div>



        </td>



        <td class="p-3.5 text-center">



          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${ev.category === 'Padang' ? 'bg-amber-100 text-amber-800' : (ev.category === 'Sukaneka' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800')}">



            ${ev.category}



          </span>



          <div class="text-[10px] text-slate-600 font-semibold mt-0.5">${ev.gender} • ${ev.grade_level}</div>



        </td>



        <td class="p-3.5 text-center">



          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${ev.event_type === 'Kumpulan' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'}">



            ${ev.event_type || 'Individu'}



          </span>



        </td>



        <td class="p-3.5 text-center font-bold text-navy-950">



          ${ev.participants_count || 0} Murid



        </td>



        <td class="p-3.5">



          ${ev.school_record_value ? `



            <div class="font-bold text-purple-950 flex items-center space-x-1">



              <i data-lucide="zap" class="w-3.5 h-3.5 text-purple-600"></i>



              <span class="font-mono text-xs">${ev.school_record_value}</span>



            </div>



            <div class="text-[10px] text-slate-500">${ev.school_record_holder || '-'} (${ev.school_record_year || '-'})</div>



          ` : '<span class="text-slate-400 text-[11px] italic">Tiada Rekod</span>'}



        </td>



        <td class="p-3.5 text-center">



          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${ev.status === 'Selesai' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">



            ${ev.status || 'Pendaftaran'}



          </span>



        </td>



        <td class="p-3.5 text-center">



          <div class="flex items-center justify-center space-x-1">



            <button onclick="app.quickOpenLanesForEvent(${ev.id})" title="Jana & Lihat Lorong" class="p-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg transition">



              <i data-lucide="flag" class="w-3.5 h-3.5"></i>



            </button>



            <button onclick="app.quickOpenResultsForEvent(${ev.id})" title="${ev.status === 'Selesai' ? 'Kemaskini / Edit Keputusan' : 'Masukkan Keputusan'}" class="p-1.5 ${ev.status === 'Selesai' ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' : 'bg-amber-50 text-amber-700 hover:bg-amber-100'} rounded-lg transition">



              <i data-lucide="${ev.status === 'Selesai' ? 'edit-3' : 'medal'}" class="w-3.5 h-3.5"></i>



            </button>



            ${(ev.status === 'Selesai' && this.canDelete()) ? `



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



            ` : ''}



          </div>



        </td>



      </tr>



    `).join("");







    lucide.createIcons();



  },







  filterSportsEventsTable() {



    const cat = document.getElementById("filter-sd-event-cat")?.value;



    const gnd = document.getElementById("filter-sd-event-gender")?.value;







    let filtered = state.sportsEvents || [];



    if (cat) filtered = filtered.filter(e => e.category === cat);



    if (gnd) filtered = filtered.filter(e => e.gender === gnd || e.gender === "Campuran");







    this.renderSportsEventsTable(filtered);



  },







  openAddSportsEventModal(eventId = null) {



    const title = document.getElementById("modal-sports-event-title");



    const editId = document.getElementById("event-edit-id");



    const nameInput = document.getElementById("event-name-input");



    const catInput = document.getElementById("event-cat-input");



    const genderInput = document.getElementById("event-gender-input");



    const gradeInput = document.getElementById("event-grade-level-input");



    const typeInput = document.getElementById("event-type-input");



    const metricInput = document.getElementById("event-metric-type");



    const recHolder = document.getElementById("event-rec-holder");



    const recVal = document.getElementById("event-rec-val");



    const recYear = document.getElementById("event-rec-year");







    if (eventId) {



      const ev = (state.sportsEvents || []).find(e => e.id === eventId);



      if (ev) {



        if (title) title.innerText = "Kemaskini Acara Sukan";



        if (editId) editId.value = ev.id;



        if (nameInput) nameInput.value = ev.event_name;



        if (catInput) catInput.value = ev.category;



        if (genderInput) genderInput.value = ev.gender;



        if (gradeInput) gradeInput.value = ev.grade_level;



        if (typeInput) typeInput.value = ev.event_type || "Individu";



        if (metricInput) metricInput.value = ev.metric_type || "Masa (Saat)";



        if (recHolder) recHolder.value = ev.school_record_holder || "";



        if (recVal) recVal.value = ev.school_record_value || "";



        if (recYear) recYear.value = ev.school_record_year || "";



      }



    } else {



      if (title) title.innerText = "Daftar Acara Sukan Baharu";



      if (editId) editId.value = "";



      if (nameInput) nameInput.value = "";



      if (recHolder) recHolder.value = "";



      if (recVal) recVal.value = "";



      if (recYear) recYear.value = "2024";



    }







    const modal = document.getElementById("modal-add-sports-event");



    if (modal) modal.classList.remove("hidden");



  },







  async handleSaveSportsEventForm(e) {



    e.preventDefault();



    const editId = document.getElementById("event-edit-id")?.value;



    const body = {



      event_name: document.getElementById("event-name-input")?.value,



      category: document.getElementById("event-cat-input")?.value || "Balapan",



      gender: document.getElementById("event-gender-input")?.value || "Lelaki",



      grade_level: document.getElementById("event-grade-level-input")?.value || "Tahap 2",



      event_type: document.getElementById("event-type-input")?.value || "Individu",



      metric_type: document.getElementById("event-metric-type")?.value || "Masa (Saat)",



      school_record_holder: document.getElementById("event-rec-holder")?.value || null,



      school_record_value: document.getElementById("event-rec-val")?.value || null,



      school_record_year: document.getElementById("event-rec-year")?.value || null,



      event_date: "2026-07-15",



      academic_year: "2026/2027"



    };







    try {



      const url = editId ? `/api/sports/events?event_id=${editId}` : "/api/sports/events";



      const res = await fetch(url, {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(body)



      });



      if (res.ok) {



        this.closeModal("modal-add-sports-event");



        await this.loadSportsDayEventsList();



        this.showToast("Acara sukan berjaya disimpan!");



      } else {



        alert("Gagal menyimpan acara sukan.");



      }



    } catch (err) {



      console.error(err);



      alert("Ralat semasa menyimpan.");



    }



  },







  async deleteSportsEvent(eventId) {



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



  },







  // ==========================================



  // PENDAFTARAN ACARA RUMAH SUKAN



  // ==========================================



  async loadSportsDayEnrollmentView() {



    try {



      const houseSelect = document.getElementById("enrollment-house-select");



      if (houseSelect) {



        const houses = (state.organizations || []).filter(o => o.category === "Rumah Sukan");



        houseSelect.innerHTML = houses.map(h => `



          <option value="${h.id}">${h.name}</option>



        `).join("");



      }







      const selectedHouseId = houseSelect?.value || (state.organizations.find(o => o.category === "Rumah Sukan")?.id);



      if (selectedHouseId) {



        await this.fetchHouseEnrollmentData(selectedHouseId);



      }



    } catch (err) {



      console.error(err);



    }



  },







  async onEnrollmentHouseChange() {



    const houseId = document.getElementById("enrollment-house-select")?.value;



    if (houseId) await this.fetchHouseEnrollmentData(houseId);



  },







  async fetchHouseEnrollmentData(houseId) {



    try {



      const res = await fetch(`/api/sports/house-enrollments/${houseId}`);



      if (!res.ok) return;



      state.sportsHouseEnrollmentData = await res.json();



      this.renderHouseStudentsEnrollmentTable();



    } catch (err) {



      console.error(err);



    }



  },







  renderHouseStudentsEnrollmentTable() {



    const data = state.sportsHouseEnrollmentData;



    const tbody = document.getElementById("sd-enrollment-table-body");



    const badge = document.getElementById("enrollment-stats-badge");



    const gradeFilter = document.getElementById("enrollment-grade-filter")?.value;







    if (!data || !tbody) return;







    let students = data.students || [];



    if (gradeFilter === "tahap1") students = students.filter(s => s.grade <= 3);



    else if (gradeFilter === "tahap2") students = students.filter(s => s.grade >= 4);







    const events = data.events || [];







    if (badge) {



      const totalEnrolled = students.filter(s => s.enrolled_events && s.enrolled_events.length > 0).length;



      badge.innerText = `${totalEnrolled} / ${students.length} Murid Didaftarkan Acara`;



    }







    if (students.length === 0) {



      tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-400">Tiada murid dijumpai untuk kriteria ini.</td></tr>`;



      return;



    }







    tbody.innerHTML = students.map((st, idx) => {



      // Eligible events matching student gender or open/relay



      const eligibleEvents = events.filter(e => (e.gender === st.gender || e.gender === "Campuran" || e.event_type === "Kumpulan"));



      const enrolledCount = (st.enrolled_events || []).length;







      return `



        <tr class="hover:bg-slate-50 transition border-b border-slate-100">



          <td class="p-3 text-center font-bold text-slate-500">${idx + 1}</td>



          <td class="p-3">



            <div class="font-black text-navy-950">${st.full_name}</div>



            <div class="text-[10px] text-slate-500 font-semibold">${st.class_name} • ${st.gender} • No. KP: ${st.ic_number || '-'}</div>



          </td>



          <td class="p-3 text-center">



            <input type="text" value="${st.bib_number || ''}" onchange="app.updateStudentBib(${st.id}, this.value)" placeholder="Bib" class="w-16 py-1 px-1.5 border border-slate-300 rounded text-center text-xs font-mono font-bold">



          </td>



          <td class="p-3">



            <div class="flex flex-wrap gap-1.5 max-w-xl">



              ${eligibleEvents.map(ev => {



                const isChecked = (st.enrolled_events || []).includes(ev.id);



                return `



                  <label class="inline-flex items-center space-x-1 px-2 py-1 rounded-lg border text-[11px] font-semibold cursor-pointer transition select-none ${isChecked ? 'bg-navy-900 text-white border-navy-950 shadow-xs' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'}">



                    <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="app.toggleStudentEventEnrollment(${st.id}, ${ev.id})" class="rounded text-navy-800 focus:ring-0">



                    <span>${ev.event_name}</span>



                  </label>



                `;



              }).join("")}



            </div>



          </td>



          <td class="p-3 text-center font-black ${enrolledCount > 0 ? 'text-navy-950' : 'text-slate-300'}">



            ${enrolledCount} Acara



          </td>



        </tr>



      `;



    }).join("");







    lucide.createIcons();



  },







  updateStudentBib(studentId, bib) {



    if (!state.sportsHouseEnrollmentData) return;



    const st = state.sportsHouseEnrollmentData.students.find(s => s.id === studentId);



    if (st) st.bib_number = bib;



  },







  toggleStudentEventEnrollment(studentId, eventId) {



    if (!state.sportsHouseEnrollmentData) return;



    const st = state.sportsHouseEnrollmentData.students.find(s => s.id === studentId);



    if (!st) return;







    st.enrolled_events = st.enrolled_events || [];



    const idx = st.enrolled_events.indexOf(eventId);



    if (idx >= 0) st.enrolled_events.splice(idx, 1);



    else st.enrolled_events.push(eventId);







    this.renderHouseStudentsEnrollmentTable();



  },







  async saveHouseEnrollments() {



    const data = state.sportsHouseEnrollmentData;



    if (!data || !data.house) return;







    const payload = {



      sport_house_id: data.house.id,



      enrollments: (data.students || []).map(s => ({



        student_id: s.id,



        event_ids: s.enrolled_events || [],



        bib_number: s.bib_number || null



      }))



    };







    try {



      const res = await fetch("/api/sports/house-enrollments", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });



      if (res.ok) {



        this.showToast("Pendaftaran acara murid berjaya disimpan!");



        await this.loadSportsDayEventsList();



      } else {



        alert("Gagal menyimpan pendaftaran acara.");



      }



    } catch (err) {



      console.error(err);



      alert("Ralat semasa menyimpan.");



    }



  },







  // ==========================================



  // JANAAN LORONG & START LIST



  // ==========================================



  async loadSportsDayLanesView() {



    try {



      if (!state.sportsEvents || state.sportsEvents.length === 0) {



        const res = await fetch("/api/sports/events");



        if (res.ok) state.sportsEvents = await res.json();



      }







      const select = document.getElementById("lanes-event-select");



      if (select) {



        select.innerHTML = (state.sportsEvents || []).map(e => `



          <option value="${e.id}">${e.event_name} (${e.category} • ${e.gender})</option>



        `).join("");



      }







      const selectedEventId = select?.value || (state.sportsEvents[0]?.id);



      if (selectedEventId) {



        await this.fetchEventStartList(selectedEventId);



      }



    } catch (err) {



      console.error(err);



    }



  },







  quickOpenLanesForEvent(eventId) {



    this.switchSportsDaySubTab("lanes");



    const select = document.getElementById("lanes-event-select");



    if (select) select.value = eventId;



    this.fetchEventStartList(eventId);



  },







  async onLanesEventSelectChange() {



    const eventId = document.getElementById("lanes-event-select")?.value;



    if (eventId) await this.fetchEventStartList(eventId);



  },







  async fetchEventStartList(eventId) {



    try {



      const res = await fetch(`/api/sports/start-list/${eventId}`);



      if (!res.ok) return;



      state.sportsCurrentStartListData = await res.json();



      this.renderEventLanesTable();



    } catch (err) {



      console.error(err);



    }



  },







  renderEventLanesTable() {



    const data = state.sportsCurrentStartListData;



    if (!data) return;







    const ev = data.event;



    const participants = data.participants || [];







    const title = document.getElementById("lanes-event-title");



    const meta = document.getElementById("lanes-event-meta");



    const recBadge = document.getElementById("lanes-school-record-badge");



    const tbody = document.getElementById("sd-lanes-table-body");







    if (title) title.innerText = ev.event_name;



    if (meta) meta.innerText = `Kategori: ${ev.category} • ${ev.grade_level} • ${ev.gender} • Jenis: ${ev.event_type || 'Individu'} • ${participants.length} Peserta`;



    if (recBadge) {



      recBadge.innerHTML = ev.school_record_value ? 



        `⚡ Rekod Sekolah: <b>${ev.school_record_value}</b> (${ev.school_record_holder || '-'}, ${ev.school_record_year || '-'})` :



        `⚡ Rekod Sekolah: <i>Tiada Rekod</i>`;



    }







    if (!tbody) return;







    if (participants.length === 0) {



      tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-slate-400">Tiada peserta didaftarkan untuk acara ini. Sila daftar peserta di tab "Pendaftaran Rumah Sukan".</td></tr>`;



      return;



    }







    tbody.innerHTML = participants.map(p => `



      <tr class="hover:bg-slate-50 transition border-b border-slate-100">



        <td class="p-3.5 text-center font-black text-sm text-navy-950">



          <span class="w-8 h-8 rounded-full bg-navy-100 text-navy-900 inline-flex items-center justify-center font-black">



            ${p.lane_number || '-'}



          </span>



        </td>



        <td class="p-3.5 text-center font-mono font-bold text-slate-800">${p.bib_number || '-'}</td>



        <td class="p-3.5">



          <div class="font-black text-navy-950">${p.full_name}</div>



          <div class="text-[10px] text-slate-500 font-semibold">No. KP: ${p.ic_number || '-'}</div>



        </td>



        <td class="p-3.5 text-center font-bold text-slate-700">${p.class_name}</td>



        <td class="p-3.5">



          <div class="flex items-center space-x-1.5 font-bold text-xs">



            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${p.house_color || '#64748b'};"></span>



            <span>${p.sport_house_name}</span>



          </div>



        </td>



        <td class="p-3.5 text-center">



          <span class="inline-block w-24 h-6 border-b-2 border-dashed border-slate-400 font-mono text-xs"></span>



        </td>



        <td class="p-3.5 text-center">



          <span class="inline-block w-12 h-6 border-b-2 border-dashed border-slate-400"></span>



        </td>



      </tr>



    `).join("");







    lucide.createIcons();



  },







  async generateCurrentEventLanes() {



    const eventId = document.getElementById("lanes-event-select")?.value;



    if (!eventId) return;







    try {



      const res = await fetch(`/api/sports/generate-lanes/${eventId}`, { method: "POST" });



      if (res.ok) {



        this.showToast("Janaan susunan lorong & giliran berjaya!");



        await this.fetchEventStartList(eventId);



      } else {



        const err = await res.json();



        alert(err.detail || "Gagal menjana lorong.");



      }



    } catch (err) {



      console.error(err);



    }



  },







  printCurrentEventStartList() {



    const data = state.sportsCurrentStartListData;



    if (!data) return;







    const ev = data.event;



    const participants = data.participants || [];



    const school = data.school || state.schoolSettings || {};







    const html = `



      <!DOCTYPE html>



      <html>



      <head>



        <title>Borang Pelepasan & Lorong - ${ev.event_name}</title>



        <meta charset="utf-8">



        <style>



          @page { size: A4 portrait; margin: 12mm 15mm; }



          body { font-family: Arial, sans-serif; font-size: 11px; color: #1e293b; margin: 0; padding: 0; line-height: 1.3; }



          .header-table { width: 100%; border-bottom: 2px solid #0f172a; padding-bottom: 6px; margin-bottom: 12px; }



          .title-box { text-align: center; margin-bottom: 14px; }



          .title-box h2 { margin: 0; font-size: 15px; text-transform: uppercase; color: #0f172a; }



          .title-box p { margin: 2px 0 0; font-size: 11px; font-weight: bold; color: #475569; }



          .meta-grid { display: flex; justify-content: space-between; background: #f8fafc; border: 1px solid #cbd5e1; padding: 6px 10px; border-radius: 6px; margin-bottom: 12px; font-size: 11px; }



          table.data-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }



          table.data-table th, table.data-table td { border: 1px solid #94a3b8; padding: 5px 8px; text-align: left; }



          table.data-table th { background: #f1f5f9; font-weight: bold; text-align: center; font-size: 10px; text-transform: uppercase; }



          .rec-box { border: 1px dashed #6b21a8; background: #faf5ff; padding: 5px 10px; border-radius: 6px; margin-bottom: 12px; font-size: 11px; font-weight: bold; color: #581c87; }



          .sig-table { width: 100%; margin-top: 25px; border-collapse: collapse; }



          .sig-table td { width: 33%; vertical-align: top; border: none; padding: 0 10px; }



          .sig-line { border-bottom: 1px dotted #000; height: 40px; margin-bottom: 4px; }



          @media print { body { -webkit-print-color-adjust: exact; } }



        </style>



      </head>



      <body>



        <table class="header-table">



          <tr>



            <td style="width: 70px; vertical-align: top;">



              <img src="/static/images/logo.png" style="max-height: 55px; max-width: 55px;" onerror="this.style.display='none'">



            </td>



            <td style="vertical-align: top; text-align: right; font-size: 10px; color: #334155;">



              <div style="font-weight: 900; font-size: 12px; color: #0f172a;">${school.school_name || 'SEKOLAH KEBANGSAAN SUNGAI DENDANG'}</div>



              <div>${school.school_address || '34140 RANTAU PANJANG, SELAMA, PERAK'}</div>



              <div>Kod Sekolah: ${school.school_code || 'ABA6034'} • Tel: ${school.phone_number || '05-8394211'}</div>



            </td>



          </tr>



        </table>







        <div class="title-box">



          <h2>BORANG PELEPASAN, SUSUNAN LORONG & GILIRAN HAKIM</h2>



          <p>KEJOHANAN SUKAN TAHUNAN SESI 2026/2027</p>



        </div>







        <div class="meta-grid">



          <div><b>Acara:</b> ${ev.event_name}</div>



          <div><b>Kategori:</b> ${ev.category} (${ev.gender})</div>



          <div><b>Tahap:</b> ${ev.grade_level}</div>



          <div><b>Masa/Tarikh:</b> ${ev.event_date || '2026-07-15'}</div>



        </div>







        ${ev.school_record_value ? `



          <div class="rec-box">



            ⚡ REKOD SEKOLAH SEDIA ADA: ${ev.school_record_value} oleh ${ev.school_record_holder || '-'} (${ev.school_record_year || '-'})



          </div>



        ` : ''}







        <table class="data-table">



          <thead>



            <tr>



              <th style="width: 30px;">Lorong</th>



              <th style="width: 50px;">No. Bib</th>



              <th>Nama Peserta</th>



              <th style="width: 60px;">Kelas</th>



              <th style="width: 120px;">Rumah Sukan</th>



              <th style="width: 100px;">Catatan Masa / Jarak</th>



              <th style="width: 50px;">Kedudukan</th>



              <th style="width: 80px;">Catatan Hakim</th>



            </tr>



          </thead>



          <tbody>



            ${participants.map(p => `



              <tr>



                <td style="text-align: center; font-weight: bold; font-size: 12px;">${p.lane_number || '-'}</td>



                <td style="text-align: center; font-family: monospace; font-weight: bold;">${p.bib_number || '-'}</td>



                <td style="font-weight: bold;">${p.full_name}</td>



                <td style="text-align: center;">${p.class_name}</td>



                <td>${p.sport_house_name}</td>



                <td></td>



                <td></td>



                <td></td>



              </tr>



            `).join("")}



          </tbody>



        </table>







        <table class="sig-table">



          <tr>



            <td>



              <div>Hakim Pelepasan / Starter:</div>



              <div class="sig-line"></div>



              <div>Nama:</div>



            </td>



            <td>



              <div>Ketua Hakim Penamat:</div>



              <div class="sig-line"></div>



              <div>Nama:</div>



            </td>



            <td>



              <div>Pengurus Kejohanan / Setiausaha Sukan:</div>



              <div class="sig-line"></div>



              <div>Nama: EN. MOHD SYAKIR BIN ZAKARIA</div>



            </td>



          </tr>



        </table>







        <script>window.onload = () => window.print();</script>



      </body>



      </html>



    `;







    const printWin = window.open("", "_blank");



    printWin.document.write(html);



    printWin.document.close();



  },







  // ==========================================



  // KEMASUKAN KEPUTUSAN & PECAH REKOD



  // ==========================================



  async loadSportsDayResultsView() {



    try {



      if (!state.sportsEvents || state.sportsEvents.length === 0) {



        const res = await fetch("/api/sports/events");



        if (res.ok) state.sportsEvents = await res.json();



      }







      const select = document.getElementById("results-event-select");



      if (select) {



        select.innerHTML = (state.sportsEvents || []).map(e => `



          <option value="${e.id}">${e.event_name} (${e.category} • ${e.gender})</option>



        `).join("");



      }







      const selectedEventId = select?.value || (state.sportsEvents[0]?.id);



      if (selectedEventId) {



        await this.prepareResultsFormForEvent(selectedEventId);



      }



    } catch (err) {



      console.error(err);



    }



  },







  quickOpenResultsForEvent(eventId) {



    this.switchSportsDaySubTab("results");



    const select = document.getElementById("results-event-select");



    if (select) select.value = eventId;



    this.prepareResultsFormForEvent(eventId);



  },







  async onResultsEventSelectChange() {



    const eventId = document.getElementById("results-event-select")?.value;



    if (eventId) await this.prepareResultsFormForEvent(eventId);



  },







  async prepareResultsFormForEvent(eventId) {



    try {



      const res = await fetch(`/api/sports/start-list/${eventId}`);



      if (!res.ok) return;



      const data = await res.json();



      const ev = data.event;



      const participants = data.participants || [];







      // Update school record notice



      const recText = document.getElementById("results-current-record-text");



      if (recText) {



        recText.innerText = ev.school_record_value ? 



          `${ev.school_record_value} oleh ${ev.school_record_holder || '-'} (${ev.school_record_year || '-'})` : 



          'Tiada Rekod Terdahulu';



      }







      // Populate student dropdowns 1 to 4



      const studentsOptions = (participants.length > 0 ? participants : (state.students || [])).map(s => `



        <option value="${s.student_id || s.id}">${s.full_name} (${s.sport_house_name || s.class_name})</option>



      `).join("");







      for (let r = 1; r <= 4; r++) {



        const stSelect = document.getElementById(`res-st-${r}`);



        const valInput = document.getElementById(`res-val-${r}`);



        if (stSelect) {



          stSelect.innerHTML = `<option value="">-- Pilih Pemenang --</option>` + studentsOptions;



        }



        if (valInput) valInput.value = "";



      }







      // Pre-fill existing results if any



      const existingRes = (state.sportsEvents || []).find(e => e.id === Number(eventId))?.results || [];



      existingRes.forEach(r => {



        const stSelect = document.getElementById(`res-st-${r.position_rank}`);



        const valInput = document.getElementById(`res-val-${r.position_rank}`);



        if (stSelect) stSelect.value = r.student_id;



        if (valInput) valInput.value = r.record_metric || "";



      });







      const btnDel = document.getElementById("btn-delete-event-results");



      if (btnDel) {



        if (this.canDelete() && existingRes.length > 0) {



          btnDel.classList.remove("hidden");



        } else {



          btnDel.classList.add("hidden");



        }



      }







      this.checkRecordBrokenPreview();



    } catch (err) {



      console.error(err);



    }



  },







  checkRecordBrokenPreview() {



    const eventId = document.getElementById("results-event-select")?.value;



    const ev = (state.sportsEvents || []).find(e => e.id === Number(eventId));



    const val1 = document.getElementById("res-val-1")?.value;



    const badge = document.getElementById("res-broken-badge-1");







    if (!ev || !val1 || !ev.school_record_num || !badge) {



      if (badge) badge.classList.add("hidden");



      return;



    }







    const num1 = parseFloat(val1.replace(/[^\d.]/g, ""));



    if (isNaN(num1)) {



      badge.classList.add("hidden");



      return;



    }







    let isBroken = false;



    if ((ev.metric_type || "").includes("Masa")) {



      if (num1 < ev.school_record_num) isBroken = true;



    } else {



      if (num1 > ev.school_record_num) isBroken = true;



    }







    if (isBroken) badge.classList.remove("hidden");



    else badge.classList.add("hidden");



  },







  async saveEventResultsEntry() {



    const eventId = document.getElementById("results-event-select")?.value;



    if (!eventId) return;







    const placings = [];



    for (let r = 1; r <= 4; r++) {



      const stId = document.getElementById(`res-st-${r}`)?.value;



      const metric = document.getElementById(`res-val-${r}`)?.value;



      if (stId) {



        placings.push({



          position_rank: r,



          student_id: Number(stId),



          record_metric: metric || null,



          remarks: `Pemenang Tempat Ke-${r}`



        });



      }



    }







    if (placings.length === 0) {



      alert("Sila pilih sekurang-kurangnya pemenang Tempat Pertama.");



      return;



    }







    try {



      const res = await fetch("/api/sports/record-results", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify({



          event_id: Number(eventId),



          placings: placings



        })



      });







      if (res.ok) {



        const data = await res.json();



        if (data.record_broken) {



          alert("⚡ TAHNIAH! REKOD SEKOLAH BERJAYA DIPERBAHARUI OLEH PEMENANG EMAS!\nMata bonus +2 telah ditambah kepada rumah sukan pemenang.");



        } else {



          this.showToast("Keputusan acara sukan berjaya direkodkan!");



        }



        await this.loadSportsDayEventsList();



        this.switchSportsDaySubTab("standings");



      } else {



        alert("Gagal merekodkan keputusan.");



      }



    } catch (err) {



      console.error(err);



      alert("Ralat semasa menyimpan keputusan.");



    }



  },







  async deleteCurrentEventResults() {



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



        this.showNotification(`Keputusan ${evName} berjaya dipadam!`, 'success');



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



  },







  // ==========================================



  // TETAPAN MARKAH KEJOHANAN



  // ==========================================



  async openSportsScoringModal() {



    try {



      const res = await fetch("/api/sports/scoring-settings");



      if (res.ok) {



        const s = await res.json();



        const ind1 = document.getElementById("score-ind-1");



        const ind2 = document.getElementById("score-ind-2");



        const ind3 = document.getElementById("score-ind-3");



        const ind4 = document.getElementById("score-ind-4");



        const grp1 = document.getElementById("score-grp-1");



        const grp2 = document.getElementById("score-grp-2");



        const grp3 = document.getElementById("score-grp-3");



        const grp4 = document.getElementById("score-grp-4");



        const recB = document.getElementById("score-rec-bonus");



        const incCC = document.getElementById("score-inc-cc");







        if (ind1) ind1.value = s.individual_1st || 7;



        if (ind2) ind2.value = s.individual_2nd || 5;



        if (ind3) ind3.value = s.individual_3rd || 3;



        if (ind4) ind4.value = s.individual_4th || 1;



        if (grp1) grp1.value = s.group_1st || 14;



        if (grp2) grp2.value = s.group_2nd || 10;



        if (grp3) grp3.value = s.group_3rd || 6;



        if (grp4) grp4.value = s.group_4th || 2;



        if (recB) recB.value = s.record_broken_bonus || 2;



        if (incCC) incCC.value = s.include_cross_country !== undefined ? s.include_cross_country : 1;



      }



      const modal = document.getElementById("modal-sports-scoring");



      if (modal) modal.classList.remove("hidden");



    } catch (err) {



      console.error(err);



    }



  },







  async handleSaveSportsScoringForm(e) {



    e.preventDefault();



    const payload = {



      individual_1st: Number(document.getElementById("score-ind-1")?.value || 7),



      individual_2nd: Number(document.getElementById("score-ind-2")?.value || 5),



      individual_3rd: Number(document.getElementById("score-ind-3")?.value || 3),



      individual_4th: Number(document.getElementById("score-ind-4")?.value || 1),



      group_1st: Number(document.getElementById("score-grp-1")?.value || 14),



      group_2nd: Number(document.getElementById("score-grp-2")?.value || 10),



      group_3rd: Number(document.getElementById("score-grp-3")?.value || 6),



      group_4th: Number(document.getElementById("score-grp-4")?.value || 2),



      record_broken_bonus: Number(document.getElementById("score-rec-bonus")?.value || 2),



      include_cross_country: Number(document.getElementById("score-inc-cc")?.value || 1)



    };







    try {



      const res = await fetch("/api/sports/scoring-settings", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });



      if (res.ok) {



        this.closeModal("modal-sports-scoring");



        this.showToast("Tetapan markah kejohanan dikemaskini!");



        await this.loadSportsDayOverview();



      }



    } catch (err) {



      console.error(err);



    }



  },







  // ==========================================



  // CETAK BUKU KEPUTUSAN & LAPORAN PENUH KEJOHANAN



  // ==========================================



  async printSportsDayFullReport() {



    try {



      const [standingsRes, eventsRes] = await Promise.all([



        fetch("/api/sports/overall-standings"),



        fetch("/api/sports/events")



      ]);







      const standings = await standingsRes.json();



      const events = await eventsRes.json();



      const school = standings.school || state.schoolSettings || {};



      const champ = standings.champion_house;



      const o1 = standings.olahragawan;



      const o2 = standings.olahragawati;







      const html = `



        <!DOCTYPE html>



        <html>



        <head>



          <title>Laporan Lengkap Kejohanan Sukan Tahunan - ${school.school_name || 'SK SUNGAI DENDANG'}</title>



          <meta charset="utf-8">



          <style>



            @page { size: A4 portrait; margin: 10mm 12mm; }



            body { font-family: Arial, sans-serif; font-size: 10px; color: #0f172a; margin: 0; padding: 0; line-height: 1.2; }



            .header-table { width: 100%; border-bottom: 2px solid #0f172a; padding-bottom: 4px; margin-bottom: 8px; }



            .title-box { text-align: center; margin-bottom: 10px; }



            .title-box h2 { margin: 0; font-size: 14px; text-transform: uppercase; color: #0f172a; }



            .title-box p { margin: 2px 0 0; font-size: 10px; font-weight: bold; color: #475569; }



            .section-title { font-size: 11px; font-weight: bold; text-transform: uppercase; color: #0f172a; background: #f1f5f9; padding: 3px 6px; border-left: 3px solid #0f172a; margin-top: 8px; margin-bottom: 4px; }



            table.data-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 9.5px; }



            table.data-table th, table.data-table td { border: 1px solid #94a3b8; padding: 3px 5px; text-align: left; }



            table.data-table th { background: #f8fafc; font-weight: bold; text-align: center; font-size: 9px; text-transform: uppercase; }



            .champ-banner { background: #fefce8; border: 1px solid #facc15; padding: 6px; border-radius: 6px; display: flex; justify-content: space-around; margin-bottom: 8px; font-size: 10px; }



            .sig-table { width: 100%; margin-top: 15px; border-collapse: collapse; font-size: 9.5px; }



            .sig-table td { width: 50%; vertical-align: top; border: none; padding: 0 10px; }



            .sig-line { border-bottom: 1px dotted #000; height: 30px; margin-bottom: 3px; }



            @media print { body { -webkit-print-color-adjust: exact; } }



          </style>



        </head>



        <body>



          <table class="header-table">



            <tr>



              <td style="width: 50px; vertical-align: top;">



                <img src="/static/images/logo.png" style="max-height: 45px; max-width: 45px;" onerror="this.style.display='none'">



              </td>



              <td style="vertical-align: top; text-align: right; font-size: 9px; color: #334155;">



                <div style="font-weight: 900; font-size: 11px; color: #0f172a;">${school.school_name || 'SEKOLAH KEBANGSAAN SUNGAI DENDANG'}</div>



                <div>${school.school_address || '34140 RANTAU PANJANG, SELAMA, PERAK'}</div>



                <div>Kod Sekolah: ${school.school_code || 'ABA6034'} • Sesi: 2026/2027</div>



              </td>



            </tr>



          </table>







          <div class="title-box">



            <h2>LAPORAN KESELURUHAN & BUKU KEPUTUSAN KEJOHANAN SUKAN TAHUNAN</h2>



            <p>GABUNGAN KUTIPAN MATA MERENTAS DESA & KEJOHANAN SUKAN TAHUNAN</p>



          </div>







          <div class="champ-banner">



            <div>🏆 <b>JUARA KESELURUHAN:</b> <span style="font-size: 11px; font-weight: 900;">${champ ? champ.name : '-'}</span> (${champ ? champ.total_points : 0} Mata)</div>



            <div>🏃‍♂️ <b>OLAHRAGAWAN:</b> <b>${o1 ? o1.full_name : '-'}</b> (${o1 ? o1.class_name : '-'})</div>



            <div>🏃‍♀️ <b>OLAHRAGAWATI:</b> <b>${o2 ? o2.full_name : '-'}</b> (${o2 ? o2.class_name : '-'})</div>



          </div>







          <div class="section-title">1. KEDUDUKAN PUNGUTAN PINGAT & MATA KESELURUHAN RUMAH SUKAN</div>



          <table class="data-table">



            <thead>



              <tr>



                <th style="width: 25px;">Ked</th>



                <th style="text-align: left;">Nama Rumah Sukan</th>



                <th>Mata Sukan</th>



                <th>Mata Merentas Desa</th>



                <th>🥇 Emas</th>



                <th>🥈 Perak</th>



                <th>🥉 Gangsa</th>



                <th>⚡ Rekod Pecah</th>



                <th>Jumlah Mata</th>



              </tr>



            </thead>



            <tbody>



              ${(standings.house_summary || []).map((h, i) => `



                <tr style="text-align: center; ${i === 0 ? 'font-weight: bold; background: #fefce8;' : ''}">



                  <td>${i + 1}</td>



                  <td style="text-align: left;">${h.name}</td>



                  <td>${h.sd_points}</td>



                  <td>${h.cc_points}</td>



                  <td>${h.total_gold}</td>



                  <td>${h.total_silver}</td>



                  <td>${h.total_bronze}</td>



                  <td>${h.sd_broken_records > 0 ? '⚡ ' + h.sd_broken_records : '-'}</td>



                  <td style="font-weight: 900; font-size: 10px;">${h.total_points}</td>



                </tr>



              `).join("")}



            </tbody>



          </table>







          <div class="section-title">2. KEPUTUSAN RASMI ACARA BALAPAN & PADANG</div>



          <table class="data-table">



            <thead>



              <tr>



                <th style="width: 20px;">Bil</th>



                <th style="text-align: left; width: 130px;">Acara Sukan</th>



                <th>🥇 Pingat Emas</th>



                <th>🥈 Pingat Perak</th>



                <th>🥉 Pingat Gangsa</th>



                <th>🏅 Ke-4</th>



              </tr>



            </thead>



            <tbody>



              ${events.map((ev, i) => {



                const g = ev.results.find(r => r.position_rank === 1);



                const s = ev.results.find(r => r.position_rank === 2);



                const b = ev.results.find(r => r.position_rank === 3);



                const f = ev.results.find(r => r.position_rank === 4);



                return `



                  <tr>



                    <td style="text-align: center; font-weight: bold;">${i + 1}</td>



                    <td>



                      <b>${ev.event_name}</b><br>



                      <span style="font-size: 8.5px; color: #64748b;">${ev.category} • ${ev.gender}</span>



                    </td>



                    <td>${g ? `<b>${g.full_name}</b> (${g.sport_house_name}) ${g.record_metric ? '[' + g.record_metric + ']' : ''} ${g.is_record_broken ? '⚡' : ''}` : '-'}</td>



                    <td>${s ? `<b>${s.full_name}</b> (${s.sport_house_name}) ${s.record_metric ? '[' + s.record_metric + ']' : ''}` : '-'}</td>



                    <td>${b ? `<b>${b.full_name}</b> (${b.sport_house_name})` : '-'}</td>



                    <td>${f ? `${f.full_name} (${f.sport_house_name})` : '-'}</td>



                  </tr>



                `;



              }).join("")}



            </tbody>



          </table>







          <table class="sig-table">



            <tr>



              <td>



                <div>Disediakan Oleh:</div>



                <div class="sig-line"></div>



                <div><b>EN. MOHD SYAKIR BIN ZAKARIA</b></div>



                <div>Setiausaha Sukan / Kokurikulum</div>



              </td>



              <td>



                <div>Disahkan Oleh:</div>



                <div class="sig-line"></div>



                <div><b>${school.headmaster_name || 'EN. AHMAD BIN ABDULLAH'}</b></div>



                <div>Guru Besar, ${school.school_name || 'SK Sungai Dendang'}</div>



              </td>



            </tr>



          </table>







          <script>window.onload = () => window.print();</script>



        </body>



        </html>



      `;







      const printWin = window.open("", "_blank");



      printWin.document.write(html);



      printWin.document.close();



    } catch (err) {



      console.error("Print full report error:", err);



    }



  },







  async loadCrossCountryOverview() {



    try {



      const res = await fetch("/api/cross-country/overview");



      if (!res.ok) return;



      const data = await res.json();



      state.crossCountryData = data;







      // 1. Render House Tally Cards



      const tallyContainer = document.getElementById("cross-country-house-tally");



      if (tallyContainer && data.house_tally) {



        tallyContainer.innerHTML = data.house_tally.map((h, idx) => `



          <div class="glass-card p-4 rounded-2xl border-l-4 shadow-sm relative overflow-hidden bg-white" style="border-left-color: ${h.color_code || '#cbd5e1'};">



            ${idx === 0 ? '<span class="absolute top-2 right-2 px-2 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] font-black rounded-full uppercase tracking-wider">🌲 Juara Merentas Desa</span>' : ''}



            <div class="text-xs font-black text-navy-950 uppercase">${h.name}</div>



            <div class="mt-2 flex items-baseline justify-between">



              <div>



                <span class="text-2xl font-black" style="color: ${h.color_code || '#1e293b'};">${h.total_points}</span>



                <span class="text-[11px] font-bold text-slate-500 ml-1">Mata</span>



              </div>



              <div class="text-right text-[11px] font-semibold text-slate-600">



                <span>${h.total_finishers || 0} Penamat</span>



              </div>



            </div>



            <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500 font-medium">



              <span>Top 15: <b>${h.top_15_finishers || 0}</b></span>



              <span>Zon 16-50: <b>${h.zone_16_50_finishers || 0}</b></span>



              ${h.broken_records_count > 0 ? `<span class="text-amber-600 font-bold">⚡ ${h.broken_records_count} Rekod</span>` : ''}



            </div>



          </div>



        `).join("");



      }







      // 2. Render Categories (Lelaki Tahap 2 & Perempuan Tahap 2)



      const catContainer = document.getElementById("cross-country-categories-container");



      if (catContainer && data.categories_data) {



        catContainer.innerHTML = data.categories_data.map(cd => {



          const cat = cd.category;



          const winners = cd.individual_winners || [];



          const zoneSummary = cd.zone_16_50_summary || {};



          const isBoy = (cat.gender === "Lelaki");







          return `



            <div class="glass-card rounded-2xl overflow-hidden shadow-sm border border-slate-200 bg-white">



              <!-- Category Header -->



              <div class="p-4 bg-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">



                <div class="flex items-center space-x-3">



                  <div class="w-9 h-9 rounded-xl ${isBoy ? 'bg-blue-600 text-blue-100' : 'bg-pink-600 text-pink-100'} flex items-center justify-center font-bold text-base">



                    ${isBoy ? '🏃‍♂️' : '🏃‍♀️'}



                  </div>



                  <div>



                    <h3 class="text-sm font-black uppercase tracking-wide text-white">Kategori: ${cat.category_name}</h3>



                    <p class="text-[11px] text-slate-300">Jarak Larian: ${cat.distance_km || 3.0} KM • Tahap 2 (Tahun 4, 5, 6)</p>



                  </div>



                </div>



                <div class="flex flex-wrap items-center gap-2">



                  <span class="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold rounded-full">



                    ${cd.total_finishers} Jumlah Penamat



                  </span>



                  <button onclick="app.editCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">



                    <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>



                    <span>Kemaskini / Edit</span>



                  </button>



                  ${this.canDelete() ? `



                  <button onclick="app.deleteCrossCountryCategoryResults('${cat.category_name}')" class="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg flex items-center space-x-1 transition shadow-xs">



                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>



                    <span>Padam Keputusan</span>



                  </button>



                  ` : ''}



                </div>



              </div>







              <!-- School Record Banner -->



              <div class="p-3 bg-amber-50 border-b border-amber-200 flex flex-wrap items-center justify-between gap-2 text-xs font-bold text-amber-950">



                <div class="flex items-center space-x-2">



                  <span class="text-base">⚡</span>



                  <span>Rekod Semasa Sekolah: <b>${cat.school_record_holder || 'Belum Ditetapkan'}</b></span>



                  <span class="font-mono text-amber-800 bg-amber-200/80 px-2 py-0.5 rounded text-[11px]">${cat.school_record_time || '-'}</span>



                  <span class="text-[10px] text-amber-700">(${cat.school_record_year || '2024'})</span>



                </div>



                <span class="text-[10px] uppercase tracking-wider bg-amber-200 text-amber-900 px-2 py-0.5 rounded-full font-black">



                  Catatan Masa Diperlukan Bagi 3 Pelari Pertama



                </span>



              </div>







              <div class="p-4 space-y-4">



                <!-- Top 15 Individual Winners Table -->



                <div>



                  <div class="flex items-center justify-between mb-2">



                    <h4 class="text-xs font-black text-navy-950 uppercase flex items-center space-x-1.5">



                      <i data-lucide="medal" class="w-4 h-4 text-amber-500"></i>



                      <span>Senarai Pemenang Individu (Kedudukan 1 hingga 15)</span>



                    </h4>



                    <span class="text-[10px] text-slate-500 font-semibold">${winners.length} / 15 Pemenang Berdaftar</span>



                  </div>







                  <div class="overflow-x-auto rounded-xl border border-slate-200">



                    <table class="w-full text-left text-xs table-custom">



                      <thead class="bg-slate-100 text-slate-700 font-bold border-b border-slate-200 text-[11px]">



                        <tr>



                          <th class="p-2.5 w-12 text-center">Ked</th>



                          <th class="p-2.5">Nama Penuh Murid & No. KP</th>



                          <th class="p-2.5 text-center w-24">Kelas</th>



                          <th class="p-2.5">Rumah Sukan</th>



                          <th class="p-2.5 text-center w-28">Catatan Masa</th>



                          <th class="p-2.5 text-center w-28">Status Rekod</th>



                          <th class="p-2.5 text-center w-16">Mata</th>



                        </tr>



                      </thead>



                      <tbody class="divide-y divide-slate-100">



                        ${winners.length === 0 ? `



                          <tr><td colspan="7" class="p-4 text-center text-slate-400 font-medium">Tiada keputusan direkodkan. Sila klik butang "+ Masukkan Keputusan".</td></tr>



                        ` : winners.map(r => `



                          <tr class="hover:bg-slate-50">



                            <td class="p-2.5 text-center font-black">



                              ${r.rank_position === 1 ? '<span class="text-yellow-600 font-black">🥇 1</span>' : (r.rank_position === 2 ? '<span class="text-slate-600 font-black">🥈 2</span>' : (r.rank_position === 3 ? '<span class="text-amber-700 font-black">🥉 3</span>' : `<span class="text-slate-700">${r.rank_position}</span>`))}



                            </td>



                            <td class="p-2.5">



                              <div class="font-bold text-slate-900">${r.full_name || '-'}</div>



                              <div class="text-[10px] text-slate-500">${r.ic_number || ''}</div>



                            </td>



                            <td class="p-2.5 text-center text-slate-700 font-semibold">${r.class_name || '-'}</td>



                            <td class="p-2.5">



                              <span class="text-xs font-bold" style="color: ${r.house_color || '#1e293b'};">${r.sport_house_name || '-'}</span>



                            </td>



                            <td class="p-2.5 text-center font-mono font-bold text-slate-700 text-xs">



                              ${r.time_recorded ? `⏱️ ${r.time_recorded}` : '<span class="text-slate-300">-</span>'}



                            </td>



                            <td class="p-2.5 text-center">



                              ${r.is_record_broken ? `



                                <span class="px-2 py-0.5 bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-black rounded-full animate-pulse">



                                  ⚡ REKOD BAHARU



                                </span>



                              ` : (r.rank_position <= 3 ? '<span class="text-[10px] text-slate-400">Rekod Kekal</span>' : '<span class="text-[10px] text-slate-300">-</span>')}



                            </td>



                            <td class="p-2.5 text-center font-black text-emerald-700 text-xs">



                              +${r.house_points}



                            </td>



                          </tr>



                        `).join("")}



                      </tbody>



                    </table>



                  </div>



                </div>







                <!-- Zone 16 to 50 Finishers Breakdown -->



                <div class="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">



                  <div class="flex items-center justify-between">



                    <h5 class="text-xs font-black text-slate-800 uppercase flex items-center space-x-1.5">



                      <i data-lucide="shield" class="w-3.5 h-3.5 text-blue-600"></i>



                      <span>Taburan Penamat Kedudukan 16 hingga 50 (Mata Rumah Sukan)</span>



                    </h5>



                    <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-bold">1 Mata Setiap Penamat</span>



                  </div>







                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">



                    ${Object.keys(zoneSummary).map(hName => {



                      const zs = zoneSummary[hName];



                      return `



                        <div class="p-2.5 bg-white border border-slate-200 rounded-xl shadow-xs flex items-center justify-between">



                          <div>



                            <div class="text-[11px] font-bold" style="color: ${zs.color_code || '#1e293b'};">${zs.house_name}</div>



                            <div class="text-[10px] text-slate-500 font-medium">${zs.finishers_count} Penamat</div>



                          </div>



                          <div class="text-right">



                            <span class="text-xs font-black text-emerald-700">+${zs.total_points}</span>



                            <span class="text-[9px] text-slate-400 block font-bold">Mata</span>



                          </div>



                        </div>



                      `;



                    }).join("")}



                  </div>



                </div>



              </div>



            </div>



          `;



        }).join("");



      }







      lucide.createIcons();



    } catch (err) {



      console.error("Load cross country overview error:", err);



    }



  },







  async editCrossCountryCategoryResults(categoryName) {



    const catSelect = document.getElementById("cc-record-category-select");



    if (catSelect) catSelect.value = categoryName;



    await this.openRecordCrossCountryModal();



  },







  async deleteCrossCountryCategoryResults(categoryName) {



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



      this.showNotification(`Keputusan bagi ${categoryName} berjaya dipadam!`, 'success');



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



  },







  // ==========================================



  // MODAL KEMASUKAN KEPUTUSAN MERENTAS DESA



  // ==========================================



  async openRecordCrossCountryModal() {



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



      this.switchCrossCountryInputTab("ind");



      await this.renderCrossCountryModalInputs();



    } catch (err) {



      console.error("Open record cross country modal error:", err);



    }



  },







  switchCrossCountryInputTab(tab) {



    state.crossCountryActiveInputTab = tab;



    const btnInd = document.getElementById("tab-btn-cc-ind");



    const btnHouse = document.getElementById("tab-btn-cc-house");



    const contentInd = document.getElementById("cc-tab-content-ind");



    const contentHouse = document.getElementById("cc-tab-content-house");







    if (tab === "ind") {



      if (btnInd) {



        btnInd.className = "pb-2.5 px-3 text-xs font-bold border-b-2 border-navy-800 text-navy-900 flex items-center space-x-1.5 transition";



      }



      if (btnHouse) {



        btnHouse.className = "pb-2.5 px-3 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-navy-900 flex items-center space-x-1.5 transition";



      }



      if (contentInd) contentInd.classList.remove("hidden");



      if (contentHouse) contentHouse.classList.add("hidden");



    } else {



      if (btnInd) {



        btnInd.className = "pb-2.5 px-3 text-xs font-bold border-b-2 border-transparent text-slate-500 hover:text-navy-900 flex items-center space-x-1.5 transition";



      }



      if (btnHouse) {



        btnHouse.className = "pb-2.5 px-3 text-xs font-bold border-b-2 border-navy-800 text-navy-900 flex items-center space-x-1.5 transition";



      }



      if (contentInd) contentInd.classList.add("hidden");



      if (contentHouse) contentHouse.classList.remove("hidden");



    }



  },







  async onCrossCountryCategorySelectChange() {



    await this.renderCrossCountryModalInputs();



  },







  async renderCrossCountryModalInputs() {



    try {



      const catSelect = document.getElementById("cc-record-category-select");



      const selectedCat = catSelect ? catSelect.value : "Lelaki (Tahap 2)";







      const res = await fetch("/api/cross-country/overview");



      if (!res.ok) return;



      const data = await res.json();



      state.crossCountryData = data;







      const catData = (data.categories_data || []).find(cd => cd.category.category_name === selectedCat) || {};



      const cat = catData.category || {};



      const winners = catData.individual_winners || [];



      const allRecs = catData.all_records || [];







      // Update current school record display



      const recDisplay = document.getElementById("cc-record-display-text");



      if (recDisplay) {



        recDisplay.textContent = cat.school_record_holder ? `${cat.school_record_holder} (${cat.school_record_time || '-'})` : 'Belum Ditetapkan';



      }







      // Fetch all students to filter eligible ones (gender match & Tahap 2 / grade >= 4)



      const stRes = await fetch("/api/students");



      const students = stRes.ok ? await stRes.json() : [];



      const isBoy = (selectedCat.includes("Lelaki"));



      const eligibleStudents = students.filter(s => {



        const genMatch = isBoy ? (s.gender === "Lelaki") : (s.gender === "Perempuan");



        return genMatch && s.grade >= 4;



      });







      // 1. Render Top 15 Individual Rows



      const indContainer = document.getElementById("cc-individual-rows-container");



      if (indContainer) {



        let html = "";



        for (let rank = 1; rank <= 15; rank++) {



          const existing = winners.find(w => w.rank_position === rank) || {};



          const isTop3 = (rank <= 3);







          html += `



            <div class="p-3 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">



              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">



                <div class="flex items-center space-x-2">



                  <span class="w-7 h-7 rounded-lg ${rank === 1 ? 'bg-yellow-100 text-yellow-800' : (rank === 2 ? 'bg-slate-200 text-slate-800' : (rank === 3 ? 'bg-amber-100 text-amber-900' : 'bg-slate-100 text-slate-700'))} flex items-center justify-center font-black text-xs">



                    ${rank === 1 ? '🥇' : (rank === 2 ? '🥈' : (rank === 3 ? '🥉' : rank))}



                  </span>



                  <span class="font-bold text-slate-800 text-xs">Tempat Ke-${rank}</span>



                </div>







                <div class="flex-1 max-w-md">



                  <select id="cc-ind-st-${rank}" class="w-full py-1.5 px-2 bg-white border border-slate-300 rounded-xl text-xs outline-none focus:ring-2 focus:ring-navy-600">



                    <option value="">-- Pilih Murid (${eligibleStudents.length} Murid Layak) --</option>



                    ${eligibleStudents.map(s => `



                      <option value="${s.id}" ${existing.student_id === s.id ? 'selected' : ''}>



                        ${s.full_name} (${s.class_name} • ${s.sport_house_name || 'Tiada Rumah'})



                      </option>



                    `).join("")}



                  </select>



                </div>







                ${isTop3 ? `



                  <div class="w-36">



                    <input type="text" id="cc-ind-time-${rank}" oninput="app.checkCrossCountryBrokenRecordLive(${cat.school_record_seconds || 0})" value="${existing.time_recorded || ''}" placeholder="cth: 14m 10s" class="w-full py-1.5 px-2 bg-white border border-slate-300 rounded-xl text-xs font-mono font-bold outline-none text-center">



                  </div>



                ` : `



                  <div class="w-36 text-center text-[10px] text-slate-400 font-medium">Masa Tidak Diperlukan</div>



                `}



              </div>







              ${rank === 1 ? `



                <div id="cc-broken-badge-live" class="${existing.is_record_broken ? '' : 'hidden'} p-1.5 bg-emerald-100 border border-emerald-300 text-emerald-900 rounded-lg text-[10px] font-black text-center animate-pulse">



                  ⚡ PECAH REKOD SEKOLAH! (+2 Mata Bonus)



                </div>



              ` : ''}



            </div>



          `;



        }



        indContainer.innerHTML = html;



      }







      // 2. Render 16 to 50 House Placings



      const houseContainer = document.getElementById("cc-house-rows-container");



      if (houseContainer) {



        const houses = (data.house_tally && data.house_tally.length > 0)



          ? data.house_tally.map(h => ({



              id: h.id,



              name: h.name,



              label: h.name.includes("Merah") ? "🔴 " + h.name.split(' ')[1] : (h.name.includes("Kuning") ? "🟡 " + h.name.split(' ')[1] : (h.name.includes("Biru") ? "🔵 " + h.name.split(' ')[1] : "🟢 " + h.name.split(' ')[1]))



            }))



          : [



              { id: 1, label: "🔴 Bendahara" },



              { id: 33, label: "🟡 Temenggong" },



              { id: 3, label: "🔵 Laksamana" },



              { id: 4, label: "🟢 Syahbandar" }



            ];







        state.crossCountryHouses = houses;







        let houseHtml = "";



        for (let rank = 16; rank <= 50; rank++) {



          const rec = allRecs.find(r => r.rank_position === rank) || {};



          const fallbackHouseId = houses[(rank - 16) % houses.length].id;



          const selectedHouseId = rec.sport_house_id || fallbackHouseId;







          houseHtml += `



            <div class="p-2 bg-white border border-slate-200 rounded-xl flex items-center justify-between shadow-2xs">



              <div class="flex items-center space-x-2">



                <span class="w-6 h-6 rounded-md bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-[11px]">${rank}</span>



                <span class="text-[11px] font-semibold text-slate-600">Penamat</span>



              </div>



              <div>



                <select id="cc-house-rank-${rank}" class="py-1 px-2 border border-slate-300 rounded-lg text-[11px] font-bold outline-none bg-white">



                  ${houses.map(h => `



                    <option value="${h.id}" ${selectedHouseId === h.id ? 'selected' : ''}>${h.label}</option>



                  `).join("")}



                </select>



              </div>



            </div>



          `;



        }



        houseContainer.innerHTML = houseHtml;



      }







      lucide.createIcons();



    } catch (err) {



      console.error("Render cross country modal inputs error:", err);



    }



  },







  checkCrossCountryBrokenRecordLive(schoolRecSeconds) {



    const timeInput = document.getElementById("cc-ind-time-1");



    const badge = document.getElementById("cc-broken-badge-live");



    if (!timeInput || !badge) return;







    const val = timeInput.value.trim().toLowerCase();



    let seconds = null;



    const mMatch = val.match(/(\d+)\s*m(?:in)?(?:\s*(\d+)\s*s)?/);



    if (mMatch) {



      seconds = parseInt(mMatch[1]) * 60 + (mMatch[2] ? parseInt(mMatch[2]) : 0);



    } else {



      const cMatch = val.match(/(\d+)[:.](\d+)/);



      if (cMatch) {



        seconds = parseInt(cMatch[1]) * 60 + parseInt(cMatch[2]);



      }



    }







    if (seconds && schoolRecSeconds > 0 && seconds < schoolRecSeconds) {



      badge.classList.remove("hidden");



    } else {



      badge.classList.add("hidden");



    }



  },







  quickFillCrossCountryHouses() {



    const houses = state.crossCountryHouses || [



      { id: 1 }, { id: 33 }, { id: 3 }, { id: 4 }



    ];



    for (let rank = 16; rank <= 50; rank++) {



      const select = document.getElementById(`cc-house-rank-${rank}`);



      if (select) {



        select.value = String(houses[(rank - 16) % houses.length].id);



      }



    }



    this.showNotification("Agihan seimbang 4 Rumah Sukan telah diisi bagi kedudukan 16 hingga 50!", "success");



  },







  async saveCrossCountryResultsSubmission() {



    try {



      const catSelect = document.getElementById("cc-record-category-select");



      const selectedCat = catSelect ? catSelect.value : "Lelaki (Tahap 2)";







      // Collect Individual Placings (1..15)



      const indPlacings = [];



      for (let rank = 1; rank <= 15; rank++) {



        const stSelect = document.getElementById(`cc-ind-st-${rank}`);



        const stId = stSelect ? parseInt(stSelect.value) : null;



        if (stId && !isNaN(stId)) {



          let timeVal = null;



          if (rank <= 3) {



            const timeInp = document.getElementById(`cc-ind-time-${rank}`);



            timeVal = timeInp ? timeInp.value.trim() : null;



          }



          indPlacings.push({



            rank_position: rank,



            student_id: stId,



            time_recorded: timeVal,



            remarks: `Pemenang Tempat Ke-${rank}`



          });



        }



      }







      if (indPlacings.length === 0) {



        alert("Sila pilih sekurang-kurangnya seorang pemenang murid individu.");



        return;



      }







      // Collect House Placings (16..50)



      const housePlacings = [];



      for (let rank = 16; rank <= 50; rank++) {



        const hSelect = document.getElementById(`cc-house-rank-${rank}`);



        if (hSelect && hSelect.value) {



          housePlacings.push({



            rank_position: rank,



            sport_house_id: parseInt(hSelect.value)



          });



        }



      }







      const payload = {



        category_name: selectedCat,



        individual_placings: indPlacings,



        house_only_placings: housePlacings



      };







      const res = await fetch("/api/cross-country/record-results", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });







      if (!res.ok) {



        const err = await res.json();



        alert("Gagal merekod keputusan: " + (err.detail || "Ralat pelayan"));



        return;



      }







      const data = await res.json();



      this.showNotification(data.message || "Keputusan Merentas Desa berjaya direkodkan!", "success");



      this.closeModal("modal-record-cross-country");



      await this.loadCrossCountryOverview();



      await this.loadSportsDayOverview();



    } catch (err) {



      console.error("Save cross country results error:", err);



      alert("Ralat semasa menyimpan keputusan merentas desa.");



    }



  },







  // ==========================================



  // MODAL TETAPAN MARKAH MERENTAS DESA



  // ==========================================



  async openCrossCountryScoringModal() {



    try {



      const res = await fetch("/api/cross-country/scoring-settings");



      if (!res.ok) return;



      const data = await res.json();







      for (let r = 1; r <= 15; r++) {



        const inp = document.getElementById(`cc-score-${r}`);



        if (inp) inp.value = data[`points_rank_${r}`] || (21 - r > 0 ? 21 - r : 1);



      }







      const inp16 = document.getElementById("cc-score-16-50");



      if (inp16) inp16.value = data.points_rank_16_to_50 || 1;







      const inpBonus = document.getElementById("cc-score-rec-bonus");



      if (inpBonus) inpBonus.value = data.record_broken_bonus || 2;







      this.openModal("modal-cross-country-scoring");



    } catch (err) {



      console.error("Open cross country scoring modal error:", err);



    }



  },







  async handleSaveCrossCountryScoringForm(e) {



    e.preventDefault();



    try {



      const payload = {



        max_individual_placings: 15,



        max_total_finishers: 50,



        points_rank_1: parseInt(document.getElementById("cc-score-1").value) || 20,



        points_rank_2: parseInt(document.getElementById("cc-score-2").value) || 18,



        points_rank_3: parseInt(document.getElementById("cc-score-3").value) || 16,



        points_rank_4: parseInt(document.getElementById("cc-score-4").value) || 14,



        points_rank_5: parseInt(document.getElementById("cc-score-5").value) || 12,



        points_rank_6: parseInt(document.getElementById("cc-score-6").value) || 10,



        points_rank_7: parseInt(document.getElementById("cc-score-7").value) || 9,



        points_rank_8: parseInt(document.getElementById("cc-score-8").value) || 8,



        points_rank_9: parseInt(document.getElementById("cc-score-9").value) || 7,



        points_rank_10: parseInt(document.getElementById("cc-score-10").value) || 6,



        points_rank_11: parseInt(document.getElementById("cc-score-11").value) || 5,



        points_rank_12: parseInt(document.getElementById("cc-score-12").value) || 4,



        points_rank_13: parseInt(document.getElementById("cc-score-13").value) || 3,



        points_rank_14: parseInt(document.getElementById("cc-score-14").value) || 2,



        points_rank_15: parseInt(document.getElementById("cc-score-15").value) || 1,



        points_rank_16_to_50: parseInt(document.getElementById("cc-score-16-50").value) || 1,



        record_broken_bonus: parseInt(document.getElementById("cc-score-rec-bonus").value) || 2



      };







      const res = await fetch("/api/cross-country/scoring-settings", {



        method: "POST",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });







      if (!res.ok) {



        alert("Gagal mengemaskini tetapan markah.");



        return;



      }







      this.showNotification("Tetapan markah Merentas Desa berjaya disimpan!", "success");



      this.closeModal("modal-cross-country-scoring");



      await this.loadCrossCountryOverview();



      await this.loadSportsDayOverview();



    } catch (err) {



      console.error("Save cross country scoring error:", err);



      alert("Ralat semasa menyimpan tetapan markah.");



    }



  },







  async printCrossCountryReport() {



    try {



      const res = await fetch("/api/cross-country/overview");



      if (!res.ok) return;



      const data = await res.json();



      const school = data.school || state.schoolSettings;



      const now = new Date().toLocaleDateString("ms-MY", { day: "numeric", month: "long", year: "numeric" });







      const html = `



        <!DOCTYPE html>



        <html>



        <head>



          <title>Keputusan Rasmi Kejohanan Merentas Desa - SK Sungai Dendang</title>



          <style>



            @page { size: A4 portrait; margin: 10mm 12mm; }



            body { font-family: 'Arial', sans-serif; color: #000; font-size: 8pt; margin: 0; line-height: 1.25; }



            .header-tbl { width: 100%; border-bottom: 2px solid #000; padding-bottom: 6px; margin-bottom: 8px; }



            .print-tbl { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 7.5pt; }



            .print-tbl th, .print-tbl td { border: 1px solid #000; padding: 3px 4px; text-align: left; }



            .print-tbl th { background-color: #f1f5f9; font-weight: bold; text-align: center; }



            .section-title { font-weight: bold; font-size: 8pt; text-transform: uppercase; margin: 6px 0 3px 0; }



            .sig-table { width: 100%; border: none; margin-top: 14px; page-break-inside: avoid; }



            .sig-table td { border: none; width: 50%; font-size: 7.5pt; vertical-align: top; }



            .sig-line { width: 160px; border-bottom: 1px solid #000; margin: 30px 0 4px 0; }



          </style>



        </head>



        <body>



          <table class="header-tbl">



            <tr>



              <td style="width: 55px; vertical-align: middle;">



                <img src="/static/images/school_logo.png" style="width: 48px; height: 48px; object-fit: contain;" onerror="this.style.display='none'">



              </td>



              <td style="text-align: center; vertical-align: middle;">



                <div style="font-size: 11pt; font-weight: 900;">${school.school_name || 'SEKOLAH KEBANGSAAN SUNGAI DENDANG'}</div>



                <div style="font-size: 7.5pt; color: #333;">${school.address || '34140 Rantau Panjang, Selama, Perak Darul Ridzuan'}</div>



                <div style="font-size: 9pt; font-weight: 900; margin-top: 3px; text-decoration: underline;">



                  KEPUTUSAN RASMI KEJOHANAN MERENTAS DESA PERINGKAT SEKOLAH TAHUN ${new Date().getFullYear()}



                </div>



              </td>



            </tr>



          </table>







          <!-- House Standings -->



          <div class="section-title">1. Kedudukan Keseluruhan Rumah Sukan (Merentas Desa)</div>



          <table class="print-tbl">



            <thead>



              <tr>



                <th style="width: 25px;">Ked</th>



                <th>Nama Rumah Sukan</th>



                <th style="width: 55px;">🥇 Emas</th>



                <th style="width: 55px;">🥈 Perak</th>



                <th style="width: 55px;">🥉 Gangsa</th>



                <th style="width: 70px;">Top 15</th>



                <th style="width: 70px;">Zon 16-50</th>



                <th style="width: 80px;">Jumlah Penamat</th>



                <th style="width: 85px;">Jumlah Mata</th>



              </tr>



            </thead>



            <tbody>



              ${(data.house_tally || []).map((h, i) => `



                <tr ${i === 0 ? 'style="font-weight: bold; background-color: #f8fafc;"' : ''}>



                  <td style="text-align: center; font-weight: bold;">${i + 1}</td>



                  <td><b>${h.name}</b> ${i === 0 ? '🌲 (JUARA MERENTAS DESA)' : ''}</td>



                  <td style="text-align: center;">${h.gold || 0}</td>



                  <td style="text-align: center;">${h.silver || 0}</td>



                  <td style="text-align: center;">${h.bronze || 0}</td>



                  <td style="text-align: center;">${h.top_15_finishers || 0}</td>



                  <td style="text-align: center;">${h.zone_16_50_finishers || 0}</td>



                  <td style="text-align: center; font-weight: bold;">${h.total_finishers || 0}</td>



                  <td style="text-align: center; font-weight: 900; font-size: 8.5pt;">${h.total_points || 0}</td>



                </tr>



              `).join("")}



            </tbody>



          </table>







          <!-- Category Top 15 Winners -->



          ${(data.categories_data || []).map(cd => {



            const cat = cd.category;



            const winners = cd.individual_winners || [];



            return `



              <div class="section-title">2. Pemenang Top 15: Kategori ${cat.category_name} (${cat.distance_km || 3.0} KM)</div>



              <div style="font-size: 7pt; margin-bottom: 2px; color: #475569;">



                Rekod Sekolah: <b>${cat.school_record_holder || '-'}</b> (${cat.school_record_time || '-'})



              </div>



              <table class="print-tbl">



                <thead>



                  <tr>



                    <th style="width: 25px;">Ked</th>



                    <th>Nama Penuh Murid</th>



                    <th style="width: 60px; text-align: center;">Kelas</th>



                    <th style="width: 120px;">Rumah Sukan</th>



                    <th style="width: 75px; text-align: center;">Catatan Masa</th>



                    <th style="width: 50px; text-align: center;">Mata</th>



                  </tr>



                </thead>



                <tbody>



                  ${winners.map(w => `



                    <tr>



                      <td style="text-align: center; font-weight: bold;">${w.rank_position}</td>



                      <td><b>${w.full_name}</b> ${w.is_record_broken ? '⚡ (PECAH REKOD)' : ''}</td>



                      <td style="text-align: center;">${w.class_name || '-'}</td>



                      <td>${w.sport_house_name || '-'}</td>



                      <td style="text-align: center; font-family: monospace;">${w.time_recorded || '-'}</td>



                      <td style="text-align: center; font-weight: bold;">+${w.house_points}</td>



                    </tr>



                  `).join("")}



                </tbody>



              </table>



            `;



          }).join("")}







          <table class="sig-table">



            <tr>



              <td>



                <div>Disediakan Oleh:</div>



                <div class="sig-line"></div>



                <div><b>EN. MOHD SYAKIR BIN ZAKARIA</b></div>



                <div>Setiausaha Sukan / Kokurikulum</div>



              </td>



              <td>



                <div>Disahkan Oleh:</div>



                <div class="sig-line"></div>



                <div><b>${school.headmaster_name || 'EN. AHMAD BIN ABDULLAH'}</b></div>



                <div>Guru Besar, ${school.school_name || 'SK Sungai Dendang'}</div>



              </td>



            </tr>



          </table>







          <script>window.onload = () => window.print();</script>



        </body>



        </html>



      `;







      const printWin = window.open("", "_blank");



      printWin.document.write(html);



      printWin.document.close();



    } catch (err) {



      console.error("Print cross country report error:", err);



    }



  },







    populatePajskClassFilter() {
    const el = document.getElementById("filter-pajsk-class");
    if (!el) return;
    const currentVal = el.value;
    const fixedClasses = ["1 UM", "2 UKM", "3 UPM", "4 USM", "5 UTM", "6 UITM"];
    el.innerHTML = `<option value="">Semua Kelas</option>` +
      fixedClasses.map(c => `<option value="${c}">${c}</option>`).join("");
    if (currentVal && fixedClasses.includes(currentVal)) {
      el.value = currentVal;
    }
  },

onPajskFilterChange() {



    if (state.pajskActiveTab === "students") {



      this.loadStudentPajskAchievements();



    } else {



      this.loadExternalEvents();



    }



  },







  async loadExternalEvents() {



    try {



      const search = document.getElementById("filter-pajsk-search")?.value || "";



      const className = document.getElementById("filter-pajsk-class")?.value || "";



      const level = document.getElementById("filter-pajsk-level")?.value || "";







      let url = "/api/pajsk/events?limit=100";



      if (search) url += `&search=${encodeURIComponent(search)}`;



      if (className) url += `&class_name=${encodeURIComponent(className)}`;



      if (level) url += `&level=${encodeURIComponent(level)}`;







      const res = await fetch(url);



      if (!res.ok) return;



      const events = await res.json();







      const tbody = document.getElementById("pajsk-events-table-body");



      if (!tbody) return;







      if (events.length === 0) {



        tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-400 font-semibold">Tiada rekod penyertaan luar didaftarkan mengikut kriteria carian.</td></tr>`;



        return;



      }







      tbody.innerHTML = events.map(ev => `



        <tr class="hover:bg-slate-50 transition">



          <td class="p-3.5">



            <div class="font-bold text-slate-900">${ev.program_name}</div>



            <div class="text-[11px] text-slate-500">${ev.event_date}</div>



          </td>



          <td class="p-3.5">



            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">



              Peringkat ${ev.participation_level}



            </span>



          </td>



          <td class="p-3.5">



            <div class="font-bold text-navy-900">${ev.org_name || '-'}</div>



            <span class="text-[10px] text-slate-500">${ev.activity_category}</span>



          </td>



          <td class="p-3.5">



            <div class="text-xs text-slate-800">${ev.venue}</div>



            <div class="text-[10px] text-slate-500">${ev.organizer}</div>



          </td>



          <td class="p-3.5 text-center">



            <div class="font-bold text-slate-900">${ev.student_count || 0} orang</div>



            ${ev.involved_classes ? `<div class="text-[10px] text-slate-500">Kelas: ${ev.involved_classes}</div>` : ''}



          </td>



          <td class="p-3.5 text-center">
            <div class="flex items-center justify-center space-x-1.5">
              <button onclick="app.openEditExternalEventModal(${ev.id})" title="Kemaskini Pencapaian & Skor Murid" class="p-1.5 text-blue-700 hover:bg-blue-100 rounded-lg transition">
                <i data-lucide="edit-3" class="w-4 h-4"></i>
              </button>
              <button onclick="app.prepareReport('student_achievements')" title="Cetak Keputusan" class="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg transition">
                <i data-lucide="printer" class="w-4 h-4"></i>
              </button>
              ${this.canDelete() ? `
              <button onclick="app.deleteExternalEvent(${ev.id}, '${(ev.program_name || '').replace(/'/g, "\\'")}')" title="Padam Rekod Pertandingan" class="p-1.5 text-rose-600 hover:bg-rose-100 rounded-lg transition">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
              </button>
              ` : ''}
            </div>
          </td>



        </tr>



      `).join("");







      lucide.createIcons();



    } catch (err) {



      console.error(err);



    }



  },







  async loadStudentPajskAchievements() {



    try {



      const search = document.getElementById("filter-pajsk-search")?.value || "";



      const className = document.getElementById("filter-pajsk-class")?.value || "";



      const level = document.getElementById("filter-pajsk-level")?.value || "";







      let url = "/api/pajsk/student-achievements?";



      if (search) url += `&search=${encodeURIComponent(search)}`;



      if (className) url += `&class_name=${encodeURIComponent(className)}`;



      if (level) url += `&level=${encodeURIComponent(level)}`;







      const res = await fetch(url);



      if (!res.ok) return;



      const students = await res.json();







      const tbody = document.getElementById("pajsk-students-table-body");



      if (!tbody) return;







      if (students.length === 0) {



        tbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-slate-400 font-semibold">Tiada data pencapaian murid ditemui untuk kriteria carian ini.</td></tr>`;



        return;



      }







      tbody.innerHTML = students.map((st, idx) => `



        <tr class="hover:bg-slate-50 transition">



          <td class="p-3.5 text-center font-bold text-slate-500">${idx + 1}</td>



          <td class="p-3.5">



            <div class="font-bold text-slate-900">${st.full_name}</div>



            <div class="text-[11px] text-slate-500 font-mono">${st.ic_number}</div>



          </td>



          <td class="p-3.5 text-center">



            <span class="px-2 py-0.5 bg-slate-100 text-slate-800 rounded-md font-semibold text-xs">${st.class_name}</span>



          </td>



          <td class="p-3.5 text-center">



            <span class="${st.gender === 'Lelaki' ? 'text-blue-600' : 'text-pink-600'} font-semibold">${st.gender}</span>



          </td>



          <td class="p-3.5 text-center font-black text-slate-800">



            ${st.total_events > 0 ? `<span class="px-2 py-0.5 bg-blue-50 text-blue-800 rounded-full font-bold">${st.total_events} program</span>` : '<span class="text-slate-400">-</span>'}



          </td>



          <td class="p-3.5 text-center">



            <span class="px-2 py-0.5 rounded-full text-xs font-bold ${st.attendance_percentage >= 80 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">



              ${st.attendance_percentage}%



            </span>



          </td>



          <td class="p-3.5">



            <div class="text-xs text-slate-700 max-w-xs truncate" title="${st.achievements_summary || 'Tiada penyertaan'}">



              ${st.achievements_summary || '<span class="text-slate-400 italic">Belum menyertai pertandingan luar</span>'}



            </div>



          </td>



          <td class="p-3.5 text-center">



            <span class="inline-flex items-center justify-center w-7 h-7 rounded-full font-black text-xs ${st.gred === 'A' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : (st.gred === 'B' ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'bg-slate-100 text-slate-700 border border-slate-300')}">



              ${st.gred}



            </span>



          </td>



          <td class="p-3.5 text-center">



            <button onclick="app.viewStudentPajsk(${st.student_id})" class="px-2.5 py-1 bg-navy-800 hover:bg-navy-900 text-white rounded-lg font-bold text-xs flex items-center space-x-1 shadow-xs transition mx-auto">



              <i data-lucide="eye" class="w-3.5 h-3.5"></i>



              <span>Lihat Pencapaian</span>



            </button>



          </td>



        </tr>



      `).join("");







      lucide.createIcons();



    } catch (err) {



      console.error("Load student achievements error:", err);



    }



  },







  async viewStudentPajsk(studentId) {



    try {



      const res = await fetch(`/api/pajsk/student/${studentId}`);



      if (!res.ok) {



        Swal.fire({ icon: 'error', title: 'Ralat', text: 'Gagal memuatkan rekod PAJSK murid.' });



        return;



      }



      const data = await res.json();



      const st = data.student;



      const events = data.events || [];







      document.getElementById("pajsk-modal-student-name").textContent = `${st.full_name} (${st.class_name})`;



      document.getElementById("pajsk-modal-student-meta").textContent = `No. KP: ${st.ic_number} • Jantina: ${st.gender} • Tahun ${st.grade}`;







      const printBtn = document.getElementById("btn-print-student-pajsk-slip");



      if (printBtn) {



        printBtn.onclick = () => app.printStudentPajskSlip(studentId);



      }







      const body = document.getElementById("pajsk-modal-student-body");



      if (body) {



        body.innerHTML = `



          <!-- Summary Header Badges (Tanpa Markah, Disertakan Kehadiran & Gred) -->



          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">



            <div class="p-3 bg-blue-50 border border-blue-200 rounded-xl text-center">



              <div class="text-[10px] text-blue-600 font-bold uppercase">Jumlah Program</div>



              <div class="text-lg font-black text-navy-950">${events.length}</div>



            </div>



            <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">



              <div class="text-[10px] text-emerald-700 font-bold uppercase">Kehadiran Mingguan</div>



              <div class="text-sm font-black text-emerald-800 mt-1">${st.attendance_text || '100%'}</div>



            </div>



            <div class="p-3 bg-purple-50 border border-purple-200 rounded-xl text-center">



              <div class="text-[10px] text-purple-600 font-bold uppercase">Peringkat Tertinggi</div>



              <div class="text-base font-black text-purple-900 mt-0.5">${data.highest_level || '-'}</div>



            </div>



            <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-center">



              <div class="text-[10px] text-amber-700 font-bold uppercase">Gred PAJSK</div>



              <div class="text-lg font-black text-amber-900">Gred ${data.gred}</div>



            </div>



          </div>







          <!-- Co-curricular Memberships & Positions Held (Jawatan Disandang) -->



          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">



            <div class="font-bold text-navy-900 uppercase text-[11px] border-b border-slate-200 pb-1 flex items-center justify-between">



              <span>Keahlian & Jawatan Disandang Dalam Organisasi Kokurikulum</span>



              <span class="text-[10px] text-slate-500 font-normal">Sesi 2026/2027</span>



            </div>



            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">



              <div class="p-2.5 bg-white rounded-lg border border-slate-200">



                <span class="text-[10px] font-bold text-slate-500 uppercase block">Rumah Sukan:</span>



                <div class="font-bold text-navy-950 mt-0.5">${st.sport_house_name || '-'}</div>



                <div class="text-[11px] mt-1"><span class="text-slate-500">Jawatan:</span> <span class="px-2 py-0.5 bg-amber-100 text-amber-900 font-bold rounded">${st.sport_house_position || 'Ahli Aktif'}</span></div>



              </div>



              <div class="p-2.5 bg-white rounded-lg border border-slate-200">



                <span class="text-[10px] font-bold text-slate-500 uppercase block">Unit Beruniform:</span>



                <div class="font-bold text-navy-950 mt-0.5">${st.uniform_unit_name || '-'}</div>



                <div class="text-[11px] mt-1"><span class="text-slate-500">Jawatan:</span> <span class="px-2 py-0.5 bg-blue-100 text-blue-900 font-bold rounded">${st.uniform_unit_position || 'Ahli Aktif'}</span></div>



              </div>



              <div class="p-2.5 bg-white rounded-lg border border-slate-200">



                <span class="text-[10px] font-bold text-slate-500 uppercase block">Kelab & Persatuan:</span>



                <div class="font-bold text-navy-950 mt-0.5">${st.club_society_name || '-'}</div>



                <div class="text-[11px] mt-1"><span class="text-slate-500">Jawatan:</span> <span class="px-2 py-0.5 bg-purple-100 text-purple-900 font-bold rounded">${st.club_society_position || 'Ahli Aktif'}</span></div>



              </div>



              <div class="p-2.5 bg-white rounded-lg border border-slate-200">



                <span class="text-[10px] font-bold text-slate-500 uppercase block">Sukan & Permainan:</span>



                <div class="font-bold text-navy-950 mt-0.5">${st.sports_game_name || '-'}</div>



                <div class="text-[11px] mt-1"><span class="text-slate-500">Jawatan:</span> <span class="px-2 py-0.5 bg-emerald-100 text-emerald-900 font-bold rounded">${st.sports_game_position || 'Ahli Aktif'}</span></div>



              </div>



            </div>



          </div>







          <!-- Detailed Events Table (Tanpa Markah) -->



          <div>



            <div class="font-bold text-navy-900 uppercase text-[11px] mb-2 flex items-center justify-between">



              <span>Senarai Pertandingan / Program Luar Disertai (${events.length})</span>



            </div>



            <div class="border border-slate-200 rounded-xl overflow-hidden shadow-xs">



              <table class="w-full text-left text-xs">



                <thead class="bg-slate-100 font-bold text-slate-700 border-b border-slate-200">



                  <tr>



                    <th class="p-2.5 w-10 text-center">Bil</th>



                    <th class="p-2.5">Program & Peringkat</th>



                    <th class="p-2.5">Tarikh & Tempat</th>



                    <th class="p-2.5">Jawatan / Peranan</th>



                    <th class="p-2.5 text-center">Pencapaian</th>



                  </tr>



                </thead>



                <tbody class="divide-y divide-slate-200">



                  ${events.length > 0 ? events.map((ev, i) => `



                    <tr class="hover:bg-slate-50">



                      <td class="p-2.5 text-center font-bold text-slate-500">${i + 1}</td>



                      <td class="p-2.5">



                        <div class="font-bold text-slate-900">${ev.program_name}</div>



                        <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 mt-0.5">



                          Peringkat ${ev.participation_level}



                        </span>



                      </td>



                      <td class="p-2.5">



                        <div class="font-semibold text-slate-800">${ev.event_date}</div>



                        <div class="text-[10px] text-slate-500">${ev.venue}</div>



                      </td>



                      <td class="p-2.5 font-semibold text-slate-700">${ev.role}</td>



                      <td class="p-2.5 text-center font-bold text-emerald-800">



                        <span class="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-md inline-block">



                          ${ev.achievement}



                        </span>



                      </td>



                    </tr>



                  `).join("") : '<tr><td colspan="5" class="p-4 text-center text-slate-400 italic">Tiada rekod program luar didaftarkan.</td></tr>'}



                </tbody>



              </table>



            </div>



          </div>



        `;



      }







      this.openModal("modal-student-pajsk");



      lucide.createIcons();



    } catch (err) {



      console.error("View student pajsk error:", err);



    }



  },







  async printStudentPajskSlip(studentId) {



    try {



      const res = await fetch(`/api/pajsk/student/${studentId}`);



      if (!res.ok) return;



      const data = await res.json();



      const st = data.student;



      const events = data.events || [];



      const school = data.school || state.schoolSettings;



      const now = new Date().toLocaleDateString("ms-MY", { day: "numeric", month: "long", year: "numeric" });







      this.closeModal("modal-student-pajsk");







      const doc = document.getElementById("print-document-container");



      doc.innerHTML = `



        <div class="single-page-sheet bg-white text-black p-6 sm:p-8 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl print:p-0 print:border-none print:shadow-none print:rounded-none" style="page-break-inside: avoid !important; min-height: 980px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">



          <div>



            <!-- Official Letterhead (Left Logo, Right Address) -->



            ${this.generateLetterheadHTML(school, "SLIP KEPUTUSAN PENTAKSIRAN KOKURIKULUM (PAJSK)", now)}







            <!-- Student Profile Header Table with Co-curricular Positions -->



            <table style="width: 100%; border: 1px solid #000000; border-collapse: collapse; margin-bottom: 8px; font-size: 8.5pt;">



              <tbody>



                <tr style="background-color: #f8fafc; border-bottom: 1px solid #000;">



                  <td style="padding: 3px 6px; width: 18%; font-weight: bold; border: 1px solid #000;">Nama Penuh:</td>



                  <td style="padding: 3px 6px; width: 32%; font-weight: 900; border: 1px solid #000; text-transform: uppercase;">${st.full_name}</td>



                  <td style="padding: 3px 6px; width: 18%; font-weight: bold; border: 1px solid #000;">No. KP / MyKid:</td>



                  <td style="padding: 3px 6px; width: 32%; font-family: monospace; font-weight: bold; border: 1px solid #000;">${st.ic_number || '-'}</td>



                </tr>



                <tr style="border-bottom: 1px solid #000;">



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Kelas:</td>



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">${st.class_name} (Tahun ${st.grade})</td>



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Jantina:</td>



                  <td style="padding: 3px 6px; border: 1px solid #000;">${st.gender}</td>



                </tr>



                <tr style="border-bottom: 1px solid #000;">



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Rumah Sukan:</td>



                  <td style="padding: 3px 6px; border: 1px solid #000;"><strong>${st.sport_house_name || '-'}</strong> (${st.sport_house_position || 'Ahli'})</td>



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Unit Beruniform:</td>



                  <td style="padding: 3px 6px; border: 1px solid #000;"><strong>${st.uniform_unit_name || '-'}</strong> (${st.uniform_unit_position || 'Ahli'})</td>



                </tr>



                <tr>



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Kelab / Persatuan:</td>



                  <td style="padding: 3px 6px; border: 1px solid #000;"><strong>${st.club_society_name || '-'}</strong> (${st.club_society_position || 'Ahli'})</td>



                  <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Sukan & Permainan:</td>



                  <td style="padding: 3px 6px; border: 1px solid #000;"><strong>${st.sports_game_name || '-'}</strong> (${st.sports_game_position || 'Ahli'})</td>



                </tr>



              </tbody>



            </table>







            <!-- PAJSK Summary Card (Tanpa Markah, Dengan Gred & Kehadiran Mingguan) -->



            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 8px; font-size: 8pt; text-align: center;">



              <div style="border: 1px solid #000; padding: 4px; background-color: #f8fafc; border-radius: 4px;">



                <div style="font-weight: bold; font-size: 7.5pt; color: #475569;">JUMLAH PROGRAM</div>



                <div style="font-size: 11pt; font-weight: 900;">${events.length}</div>



              </div>



              <div style="border: 1px solid #000; padding: 4px; background-color: #f8fafc; border-radius: 4px;">



                <div style="font-weight: bold; font-size: 7.5pt; color: #047857;">KEHADIRAN MINGGUAN</div>



                <div style="font-size: 10pt; font-weight: 900; color: #047857;">${st.attendance_text || '100%'}</div>



              </div>



              <div style="border: 1px solid #000; padding: 4px; background-color: #f8fafc; border-radius: 4px;">



                <div style="font-weight: bold; font-size: 7.5pt; color: #1d4ed8;">PERINGKAT TERTINGGI</div>



                <div style="font-size: 10pt; font-weight: 900; color: #1d4ed8;">${data.highest_level || '-'}</div>



              </div>



              <div style="border: 1px solid #000; padding: 4px; background-color: #f8fafc; border-radius: 4px;">



                <div style="font-weight: bold; font-size: 7.5pt; color: #b45309;">GRED KESELURUHAN</div>



                <div style="font-size: 11pt; font-weight: 900; color: #b45309;">GRED ${data.gred}</div>



              </div>



            </div>







            <!-- Detailed Participation Table (Tanpa Markah) -->



            <div style="margin-bottom: 8px;">



              <div style="font-weight: 900; font-size: 8.5pt; text-transform: uppercase; margin-bottom: 3px;">Rekod Butiran Pencapaian & Pertandingan Luar</div>



              <table class="print-table" style="width: 100%; border: 1px solid #000; border-collapse: collapse; font-size: 8pt;">



                <thead>



                  <tr style="background-color: #f1f5f9; font-weight: bold;">



                    <th style="border: 1px solid #000; padding: 3px 5px; width: 25px; text-align: center;">Bil</th>



                    <th style="border: 1px solid #000; padding: 3px 5px;">Nama Pertandingan / Program</th>



                    <th style="border: 1px solid #000; padding: 3px 5px; width: 80px; text-align: center;">Peringkat</th>



                    <th style="border: 1px solid #000; padding: 3px 5px; width: 95px;">Tarikh & Tempat</th>



                    <th style="border: 1px solid #000; padding: 3px 5px; width: 80px; text-align: center;">Peranan</th>



                    <th style="border: 1px solid #000; padding: 3px 5px; width: 90px; text-align: center;">Pencapaian</th>



                  </tr>



                </thead>



                <tbody>



                  ${events.length > 0 ? events.map((ev, i) => `



                    <tr>



                      <td style="border: 1px solid #000; padding: 3px 5px; text-align: center; font-weight: bold;">${i + 1}</td>



                      <td style="border: 1px solid #000; padding: 3px 5px; font-weight: bold;">${ev.program_name}</td>



                      <td style="border: 1px solid #000; padding: 3px 5px; text-align: center;">${ev.participation_level}</td>



                      <td style="border: 1px solid #000; padding: 3px 5px;">${ev.event_date}<br><span style="font-size: 7pt; color: #555;">${ev.venue}</span></td>



                      <td style="border: 1px solid #000; padding: 3px 5px; text-align: center;">${ev.role}</td>



                      <td style="border: 1px solid #000; padding: 3px 5px; text-align: center; font-weight: bold; color: #047857;">${ev.achievement}</td>



                    </tr>



                  `).join("") : `<tr><td colspan="6" style="border: 1px solid #000; padding: 12px; text-align: center; color: #777;">Tiada rekod pertandingan luar didaftarkan setakat ini.</td></tr>`}



                </tbody>



              </table>



            </div>



          </div>







          <!-- Dual Official Signatures -->



          <div class="signature-section" style="display: flex; justify-content: space-between; border-top: 1px solid #000; padding-top: 8px; margin-top: 4px; font-size: 8pt;">



            <div style="text-align: center; width: 170px;">



              <div style="font-size: 7.5pt; color: #475569; margin-bottom: 24px;">Disediakan oleh:</div>



              <div style="border-bottom: 1px solid #000;"></div>



              <div style="font-weight: bold; text-transform: uppercase; margin-top: 2px;">${school.su_koko_name || 'Setiausaha Kokurikulum'}</div>



              <div style="font-size: 7pt; color: #475569;">Setiausaha Kokurikulum</div>



            </div>







            <div style="text-align: center; width: 170px;">



              <div style="font-size: 7.5pt; color: #475569; margin-bottom: 24px;">Disahkan oleh:</div>



              <div style="border-bottom: 1px solid #000;"></div>



              <div style="font-weight: bold; text-transform: uppercase; margin-top: 2px;">${school.principal_name || 'Guru Besar'}</div>



              <div style="font-size: 7pt; color: #475569;">Guru Besar SK Sungai Dendang</div>



            </div>



          </div>



        </div>



      `;







      this.openModal("modal-print-preview");



      lucide.createIcons();



    } catch (err) {



      console.error("Print student pajsk slip error:", err);



    }



  },







  
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

  openNewExternalEventModal() {



    const modal = document.getElementById("modal-external-event");



    const form = document.getElementById("form-external-event");



    form.reset();



    document.getElementById("pajsk-form-date").value = new Date().toISOString().split("T")[0];



    document.getElementById("pajsk-form-venue").value = "PPD Larut Matang & Selama";



    document.getElementById("pajsk-form-organizer").value = "Kementerian Pendidikan Malaysia";







    state.currentPajskStudents = [];



    this.addStudentRowToPajskModal();







    modal.classList.remove("hidden");



    lucide.createIcons();



  },







  addStudentRowToPajskModal() {



    const defaultStudent = state.students[0];



    if (!defaultStudent) return;







    state.currentPajskStudents.push({



      student_id: defaultStudent.id,



      role: "Peserta",



      achievement: "Johan",



      remarks: ""



    });







    this.renderPajskModalStudentsTable();



  },







  renderPajskModalStudentsTable() {



    const tbody = document.getElementById("pajsk-modal-students-body");



    const level = document.getElementById("pajsk-form-level")?.value || "Daerah";







    tbody.innerHTML = state.currentPajskStudents.map((item, idx) => {



      const score = this.calculatePajskScoreClient(level, item.achievement, item.role);



      return `



        <tr>



          <td class="p-2.5">



            <select onchange="state.currentPajskStudents[${idx}].student_id = parseInt(this.value)" class="py-1 px-2 border rounded-lg text-xs w-48 font-bold">



              ${state.students.map(s => `<option value="${s.id}" ${s.id === item.student_id ? 'selected' : ''}>${s.full_name} (${s.class_name})</option>`).join("")}



            </select>



          </td>



          <td class="p-2.5">



            <select onchange="state.currentPajskStudents[${idx}].role = this.value; app.recalculatePajskTable()" class="py-1 px-2 border rounded-lg text-xs">



              <option value="Peserta" ${item.role === 'Peserta' ? 'selected' : ''}>Peserta</option>



              <option value="Wakil Sekolah" ${item.role === 'Wakil Sekolah' ? 'selected' : ''}>Wakil Sekolah</option>



              <option value="Jawatankuasa" ${item.role === 'Jawatankuasa' ? 'selected' : ''}>Jawatankuasa</option>



            </select>



          </td>



          <td class="p-2.5">



            <select onchange="state.currentPajskStudents[${idx}].achievement = this.value; app.recalculatePajskTable()" class="py-1 px-2 border rounded-lg text-xs font-bold text-navy-900">



              <option value="Johan" ${item.achievement === 'Johan' ? 'selected' : ''}>Johan / Emas</option>



              <option value="Naib Johan" ${item.achievement === 'Naib Johan' ? 'selected' : ''}>Naib Johan / Perak</option>



              <option value="Tempat Ketiga" ${item.achievement === 'Tempat Ketiga' ? 'selected' : ''}>Tempat Ketiga / Gangsa</option>



              <option value="Saguhati" ${item.achievement === 'Saguhati' ? 'selected' : ''}>Saguhati</option>



              <option value="Penyertaan" ${item.achievement === 'Penyertaan' ? 'selected' : ''}>Penyertaan Sahaja</option>



            </select>



          </td>



          <td class="p-2.5 text-center font-black text-emerald-700">${score}m</td>



          <td class="p-2.5 text-center">



            <button type="button" onclick="state.currentPajskStudents.splice(${idx}, 1); app.renderPajskModalStudentsTable()" class="text-rose-600 font-bold hover:underline">Buang</button>



          </td>



        </tr>



      `;



    }).join("");



  },







  recalculatePajskTable() {



    this.renderPajskModalStudentsTable();



  },







  calculatePajskScoreClient(level, achievement, role) {



    const matrix = {



      "Antarabangsa": { "Johan": 20.0, "Naib Johan": 20.0, "Tempat Ketiga": 19.0, "Saguhati": 18.0, "Penyertaan": 17.0 },



      "Kebangsaan": { "Johan": 20.0, "Naib Johan": 19.0, "Tempat Ketiga": 18.0, "Saguhati": 17.0, "Penyertaan": 16.0 },



      "Negeri": { "Johan": 17.0, "Naib Johan": 16.0, "Tempat Ketiga": 15.0, "Saguhati": 14.0, "Penyertaan": 13.0 },



      "Daerah": { "Johan": 14.0, "Naib Johan": 13.0, "Tempat Ketiga": 12.0, "Saguhati": 11.0, "Penyertaan": 10.0 },



      "Zon": { "Johan": 11.0, "Naib Johan": 10.0, "Tempat Ketiga": 9.0, "Saguhati": 8.0, "Penyertaan": 7.0 }



    };



    return matrix[level]?.[achievement] || 10.0;



  },







  async saveExternalEvent(e) {
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
  },







  async openAuditLogsModal() {



    try {



      const res = await fetch("/api/pajsk/audit-logs");



      if (!res.ok) return;



      const logs = await res.json();







      const tbody = document.getElementById("audit-logs-table-body");



      tbody.innerHTML = logs.map(l => `



        <tr class="hover:bg-slate-50">



          <td class="p-2.5 text-slate-500 font-mono text-[11px]">${l.created_at}</td>



          <td class="p-2.5 font-bold">${l.username} <span class="text-[10px] text-blue-700">(${l.user_role})</span></td>



          <td class="p-2.5"><span class="px-2 py-0.5 bg-slate-100 text-slate-800 rounded font-semibold text-[10px]">${l.action}</span></td>



          <td class="p-2.5 text-slate-700">${l.description}</td>



        </tr>



      `).join("");







      document.getElementById("modal-audit-logs").classList.remove("hidden");



      lucide.createIcons();



    } catch (e) {



      console.error(e);



    }



  },







  // ==========================================



  // VIEW 8: PUSAT LAPORAN & CETAKAN (16 TYPES)



  // ==========================================



  async prepareReport(reportType, customParams = {}) {



    try {



      state.lastGeneratedReportType = reportType;



      state.lastGeneratedReportParams = customParams;







      const q = new URLSearchParams(customParams).toString();



      const url = `/api/reports/generate/${reportType}${q ? '?' + q : ''}`;







      const res = await fetch(url);



      if (!res.ok) return;



      const report = await res.json();







      this.renderPrintDocument(report);



      document.getElementById("modal-print-preview").classList.remove("hidden");



      lucide.createIcons();



    } catch (err) {



      console.error("Report generate error:", err);



    }



  },







  openReportOptionsModal(reportType) {



    state.currentReportOptionsType = reportType;



    const titleEl = document.getElementById("report-options-title");



    const descEl = document.getElementById("report-options-desc");



    const controlsEl = document.getElementById("report-options-controls");



    document.getElementById("report-options-type").value = reportType;







    const houses = state.organizations.filter(o => o.category === "Rumah Sukan");



    const allOrgs = state.organizations;







    let titleText = "Pilihan Parameter Laporan";



    let descText = "Pilih parameter yang dikehendaki untuk dicetak atau dieksport ke Excel.";



    let html = "";







    switch (reportType) {



      case "students_by_class":



        titleText = "Senarai Murid Mengikut Kelas";



        descText = "Pilih tahun atau kelas tertentu untuk dicetak/dieksport, atau pilih 'Semua Kelas' untuk keseluruhan sekolah.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Tahun / Tingkatan</label>



            <select id="rep-opt-grade" onchange="app.updateReportOptionsClassDropdown(this.value)" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Semua Tahun (Tahun 1 - 6)</option>



              <option value="1">Tahun 1</option>



              <option value="2">Tahun 2</option>



              <option value="3">Tahun 3</option>



              <option value="4">Tahun 4</option>



              <option value="5">Tahun 5</option>



              <option value="6">Tahun 6</option>



            </select>



          </div>



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Nama Kelas (Pilihan)</label>



            <select id="rep-opt-class" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Semua Kelas Bagi Tahun Dipilih</option>



              ${state.classes.map(c => `<option value="${c.class_name}">${c.class_name}</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "members_by_org":



      case "org_chart":



      case "org_attendance":



        titleText = "Laporan Organisasi Kokurikulum";



        descText = "Pilih unit beruniform, kelab persatuan, sukan permainan atau rumah sukan yang dikehendaki.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Organisasi Kokurikulum *</label>



            <select id="rep-opt-org" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-bold text-navy-900">



              ${allOrgs.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "students_by_sport_house":



        titleText = "Senarai Murid Rumah Sukan";



        descText = "Pilih rumah sukan khusus atau pilih 'Semua Rumah Sukan' untuk laporan penuh.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Rumah Sukan</label>



            <select id="rep-opt-house" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Semua Rumah Sukan (Merah, Biru, Hijau, Kuning)</option>



              ${houses.map(h => `<option value="${h.id}">${h.name}</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "student_committees":



        titleText = "Senarai Jawatankuasa Murid (AJK)";



        descText = "Pilih kategori kokurikulum atau organisasi tertentu untuk senarai kepimpinan murid.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Kategori Kokurikulum</label>



            <select id="rep-opt-category" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Semua Kategori</option>



              <option value="Rumah Sukan">Rumah Sukan</option>



              <option value="Unit Beruniform">Unit Beruniform</option>



              <option value="Kelab & Persatuan">Kelab & Persatuan</option>



              <option value="Sukan & Permainan">Sukan & Permainan</option>



            </select>



          </div>



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Atau Pilih Organisasi Khusus</label>



            <select id="rep-opt-org" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">-- Semua Organisasi Dalam Kategori --</option>



              ${allOrgs.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "pajsk_summary_class_or_org":



        titleText = "Ringkasan PAJSK Kelas / Organisasi";



        descText = "Pilih kelas atau organisasi bagi ringkasan analisis markah PAJSK.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Tahun / Tingkatan</label>



            <select id="rep-opt-grade" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Keseluruhan Sekolah (Tahun 1 - 6)</option>



              <option value="4">Tahun 4</option>



              <option value="5">Tahun 5</option>



              <option value="6">Tahun 6</option>



            </select>



          </div>



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Atau Pilih Organisasi</label>



            <select id="rep-opt-org" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">-- Pilihan Mengikut Kelas Sahaja --</option>



              ${allOrgs.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "individual_attendance":



      case "individual_pajsk":



      case "individual_student_profile":



        titleText = "Laporan Kokurikulum Individu";



        descText = "Pilih nama murid untuk mencetak atau mengeksport rekod individu.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Murid *</label>



            <select id="rep-opt-student" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-bold text-navy-900">



              ${state.students.map(s => `<option value="${s.id}">${s.full_name} (${s.class_name} - ${s.ic_number})</option>`).join("")}



            </select>



          </div>



        `;



        break;







      case "weekly_activity":



        titleText = "Laporan Aktiviti Mingguan";



        descText = "Pilih organisasi dan julat tarikh aktiviti.";



        html = `



          <div>



            <label class="block font-bold text-slate-700 uppercase mb-1 text-[11px]">Pilih Organisasi</label>



            <select id="rep-opt-org" class="w-full py-2 px-3 border border-slate-300 rounded-xl outline-none font-semibold">



              <option value="">Semua Organisasi</option>



              ${allOrgs.map(o => `<option value="${o.id}">[${o.category}] ${o.name}</option>`).join("")}



            </select>



          </div>



          <div class="grid grid-cols-2 gap-2">



            <div>



              <label class="block font-bold text-slate-700 uppercase mb-1 text-[10px]">Dari Tarikh</label>



              <input type="date" id="rep-opt-start" class="w-full py-1.5 px-2 border rounded-lg text-xs outline-none">



            </div>



            <div>



              <label class="block font-bold text-slate-700 uppercase mb-1 text-[10px]">Hingga Tarikh</label>



              <input type="date" id="rep-opt-end" class="w-full py-1.5 px-2 border rounded-lg text-xs outline-none">



            </div>



          </div>



        `;



        break;







      default:



        titleText = "Laporan Rasmi Kokurikulum";



        descText = "Sedia untuk dicetak dengan kepala surat rasmi atau dieksport ke fail Excel.";



        html = `



          <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-600">



            Semua rekod data bagi laporan ini akan dijana secara automatik.



          </div>



        `;



        break;



    }







    titleEl.innerHTML = `<i data-lucide="sliders-horizontal" class="w-4 h-4 mr-2 text-blue-400"></i><span>${titleText}</span>`;



    descEl.textContent = descText;



    controlsEl.innerHTML = html;



    document.getElementById("modal-report-options").classList.remove("hidden");



    lucide.createIcons();



  },







  updateReportOptionsClassDropdown(grade) {



    const classEl = document.getElementById("rep-opt-class");



    if (!classEl) return;



    if (!grade) {



      classEl.innerHTML = `<option value="">Semua Kelas Bagi Tahun Dipilih</option>` + state.classes.map(c => `<option value="${c.class_name}">${c.class_name}</option>`).join("");



      return;



    }



    const filtered = state.classes.filter(c => c.grade === parseInt(grade));



    classEl.innerHTML = `<option value="">Semua Kelas Tahun ${grade}</option>` + filtered.map(c => `<option value="${c.class_name}">${c.class_name}</option>`).join("");



  },







  executeReportAction(actionType) {



    const reportType = state.currentReportOptionsType;



    const params = {};







    const gradeEl = document.getElementById("rep-opt-grade");



    const classEl = document.getElementById("rep-opt-class");



    const orgEl = document.getElementById("rep-opt-org");



    const houseEl = document.getElementById("rep-opt-house");



    const catEl = document.getElementById("rep-opt-category");



    const studentEl = document.getElementById("rep-opt-student");



    const startEl = document.getElementById("rep-opt-start");



    const endEl = document.getElementById("rep-opt-end");







    if (gradeEl && gradeEl.value) params.grade = gradeEl.value;



    if (classEl && classEl.value) params.class_name = classEl.value;



    if (orgEl && orgEl.value) params.org_id = orgEl.value;



    if (houseEl && houseEl.value) params.org_id = houseEl.value;



    if (catEl && catEl.value) params.category = catEl.value;



    if (studentEl && studentEl.value) params.student_id = studentEl.value;



    if (startEl && startEl.value) params.start_date = startEl.value;



    if (endEl && endEl.value) params.end_date = endEl.value;







    this.closeModal("modal-report-options");







    if (actionType === "print") {



      this.prepareReport(reportType, params);



    } else if (actionType === "excel") {



      const q = new URLSearchParams(params).toString();



      window.location.href = `/api/reports/export/excel/${reportType}?${q}`;



    }



  },







  exportCurrentReportExcel() {



    if (!state.lastGeneratedReportType) {



      this.exportStudentsExcel();



      return;



    }



    if (state.lastGeneratedReportType === "filtered_students") {



      const q = new URLSearchParams(state.lastGeneratedReportParams || {}).toString();



      window.location.href = `/api/students/export/excel?${q}`;



      return;



    }



    const q = new URLSearchParams(state.lastGeneratedReportParams || {}).toString();



    window.location.href = `/api/reports/export/excel/${state.lastGeneratedReportType}?${q}`;



  },







  printCurrentDocument() {



    const container = document.getElementById("print-document-container");



    if (!container) {



      window.print();



      return;



    }







    // Determine orientation: landscape if containing table-landscape or landscape-sheet



    const isLandscape = container.querySelector(".table-landscape, .landscape-sheet") !== null;



    const orientation = isLandscape ? "A4 landscape" : "A4 portrait";







    // Clone content and remove any elements marked with .no-print, buttons, scripts



    const clone = container.cloneNode(true);







    // Sync input values into clone before stripping



    const origInputs = container.querySelectorAll("input.jersey-input");



    const cloneInputs = clone.querySelectorAll("input.jersey-input");



    origInputs.forEach((inp, idx) => {



      const val = (inp.value || "").trim();



      if (cloneInputs[idx]) {



        const td = cloneInputs[idx].parentNode;



        td.innerHTML = `<span style="font-weight: bold; font-size: 9pt;">${val || '&nbsp;'}</span>`;



      }



    });







    clone.querySelectorAll(".no-print, button, script").forEach(el => el.remove());







    // Create or reuse hidden iframe



    let iframe = document.getElementById("hidden-print-iframe");



    if (!iframe) {



      iframe = document.createElement("iframe");



      iframe.id = "hidden-print-iframe";



      iframe.name = "hidden-print-iframe";



      iframe.style.position = "fixed";



      iframe.style.right = "0";



      iframe.style.bottom = "0";



      iframe.style.width = "0";



      iframe.style.height = "0";



      iframe.style.border = "none";



      iframe.style.visibility = "hidden";



      document.body.appendChild(iframe);



    }







    const doc = iframe.contentWindow.document;



    doc.open();



    doc.write(`<!DOCTYPE html>



<html>



<head>



  <meta charset="utf-8">



  <title>Cetak Dokumen Kokurikulum</title>



  <style>



    @page {



      size: ${orientation};



      margin: 8mm;



    }



    *, *::before, *::after {



      box-shadow: none !important;



      -webkit-box-shadow: none !important;



      text-shadow: none !important;



      filter: none !important;



      box-sizing: border-box !important;



    }



    html, body {



      margin: 0 !important;



      padding: 0 !important;



      background: #ffffff !important;



      color: #000000 !important;



      font-family: Arial, "Helvetica Neue", Helvetica, sans-serif !important;



      font-size: 8.8pt !important;



      width: 100% !important;



      height: auto !important;



      min-height: 0 !important;



      max-height: none !important;



      overflow: visible !important;



      -webkit-print-color-adjust: exact !important;



      print-color-adjust: exact !important;



    }



    .r01-sheet, .r02-sheet, .single-page-sheet {



      display: block !important;



      page-break-inside: avoid !important;



      break-inside: avoid !important;



      page-break-after: always !important;



      break-after: page !important;



      width: 100% !important;



      max-width: 100% !important;



      box-sizing: border-box !important;



      background: #ffffff !important;



      margin: 0 !important;



      padding: 0 !important;



      border: none !important;



      box-shadow: none !important;



    }



    .r01-sheet:last-child, .r01-sheet:last-of-type,



    .r02-sheet:last-child, .r02-sheet:last-of-type,



    .single-page-sheet:last-child, .single-page-sheet:last-of-type {



      page-break-after: auto !important;



      break-after: auto !important;



    }



    table {



      border-collapse: collapse !important;



    }



    .official-letterhead {



      border-bottom: 2px solid #000000 !important;



      padding-bottom: 6px !important;



      margin-bottom: 8px !important;



      display: flex !important;



      flex-direction: row !important;



      align-items: center !important;



      justify-content: space-between !important;



      text-align: right !important;



      width: 100% !important;



      box-sizing: border-box !important;



    }



    .official-letterhead .letterhead-logo-container {



      width: 75px !important;



      min-width: 75px !important;



      text-align: left !important;



    }



    .official-letterhead .letterhead-logo {



      width: 65px !important;



      height: 65px !important;



      object-fit: contain !important;



      margin: 0 !important;



      display: block !important;



    }



    .official-letterhead .letterhead-info {



      flex: 1 !important;



      text-align: right !important;



      padding-left: 10px !important;



      line-height: 1.25 !important;



    }



    .signature-section {



      page-break-inside: avoid !important;



      margin-top: 14px !important;



      display: flex !important;



      justify-content: space-between !important;



    }



    .print-table {



      width: 100% !important;



      border-collapse: collapse !important;



      margin-top: 12px !important;



      margin-bottom: 16px !important;



      font-size: 9.5pt !important;



    }



    .print-table th, .print-table td {



      border: 1px solid #000000 !important;



      padding: 6px 8px !important;



      text-align: left !important;



    }



    .print-table th {



      background-color: #f1f5f9 !important;



      font-weight: bold !important;



    }



  </style>



</head>



<body>



  ${clone.innerHTML}



</body>



</html>`);



    doc.close();







    // Allow images & styles in iframe to render before calling print



    setTimeout(() => {



      iframe.contentWindow.focus();



      iframe.contentWindow.print();



    }, 250);



  },







  generateLetterheadHTML(school, titleText, now) {



    return `



      <div class="official-letterhead" style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000000; padding-bottom: 6px; margin-bottom: 8px; width: 100%;">



        <div class="letterhead-logo-container" style="width: 70px; min-width: 70px; text-align: left;">



          <img src="${school.logo_url || '/static/images/school_logo.png'}" class="letterhead-logo" style="height: 65px; width: 65px; object-fit: contain;" alt="Logo Sekolah">



        </div>



        <div class="letterhead-info" style="flex: 1; text-align: right; padding-left: 10px; line-height: 1.25;">



          <div style="font-size: 8.5pt; font-weight: bold; text-transform: uppercase; color: #1e293b; letter-spacing: 0.5px;">KEMENTERIAN PENDIDIKAN MALAYSIA</div>



          <div style="font-size: 8pt; font-weight: bold; text-transform: uppercase; color: #334155;">JABATAN PENDIDIKAN NEGERI PERAK • PPD LARUT MATANG DAN SELAMA</div>



          <div style="font-size: 11pt; font-weight: 900; text-transform: uppercase; color: #0f172a; margin: 1px 0;">${school.school_name || 'SEKOLAH KEBANGSAAN SUNGAI DENDANG'}</div>



          <div style="font-size: 7.5pt; color: #475569;">${school.address || '34140 Rantau Panjang, Selama, Perak Darul Ridzuan'}</div>



          <div style="font-size: 7.5pt; color: #475569; font-weight: 600;">Kod Sekolah: ${school.school_code || 'ABA6034'} • Tel: ${school.phone || '05-8391234'} • Emel: ${school.email || 'aba6034@moe.edu.my'}</div>



        </div>



      </div>



      ${titleText ? `



        <div style="text-align: center; margin-bottom: 8px;">



          <h2 style="font-size: 10.5pt; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1.5px solid #000; display: inline-block; padding-bottom: 2px; margin: 0 0 2px 0;">${titleText}</h2>



          <div style="font-size: 7.5pt; color: #475569;">Sesi Persekolahan: ${school.session_year || '2026/2027'} • Tarikh Cetakan: ${now}</div>



        </div>



      ` : ''}



    `;



  },







  renderPrintDocument(report) {



    const doc = document.getElementById("print-document-container");



    const school = report.school || state.schoolSettings;



    const now = new Date().toLocaleDateString("ms-MY", { day: "numeric", month: "long", year: "numeric" });



    const rType = report.report_type || state.lastGeneratedReportType;







    let html = "";







    // 1. Weekly Activity Report (Each activity formatted to fit EXACTLY 1 PAGE)



    if (rType === "weekly_activity" && Array.isArray(report.data)) {



      if (report.data.length === 0) {



        html = `



          <div class="bg-white text-black p-6 sm:p-10 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl">



            ${this.generateLetterheadHTML(school, "LAPORAN AKTIVITI MINGGUAN KOKURIKULUM", now)}



            <div class="p-6 text-center text-slate-500 border border-slate-300 rounded-xl my-4">Tiada rekod laporan aktiviti mingguan ditemui untuk kriteria ini.</div>



          </div>



        `;



      } else {



        html = `



          <div class="w-full flex flex-col items-center">



            ${report.data.map((act, actIdx) => `



              ${actIdx > 0 ? `



                <div class="no-print my-6 flex items-center justify-center w-full max-w-4xl">



                  <div class="h-px bg-slate-400 flex-1"></div>



                  <span class="mx-4 px-4 py-1.5 bg-slate-800 text-white rounded-full text-xs font-bold shadow-md flex items-center space-x-1.5">



                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-blue-400"></i>



                    <span>Helaian / Laporan ${actIdx + 1}: ${act.org_name || ''} (${act.activity_date || ''})</span>



                  </span>



                  <div class="h-px bg-slate-400 flex-1"></div>



                </div>



              ` : ''}







              <div class="single-page-sheet bg-white text-black p-5 sm:p-7 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl mb-6 print:mb-0 print:p-0 print:border-none print:shadow-none print:rounded-none" style="page-break-inside: avoid !important; page-break-after: always !important; break-after: page !important; min-height: 980px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">



                <div style="width: 100%;">



                  <!-- Official Letterhead (Left Logo, Right Address) -->



                  ${this.generateLetterheadHTML(school, "LAPORAN AKTIVITI MINGGUAN KOKURIKULUM", now)}







                  <!-- Table Ringkasan Butiran Aktiviti -->



                  <table style="width: 100%; border: 1px solid #000000; border-collapse: collapse; margin-bottom: 6px; font-size: 8.2pt; line-height: 1.35;">



                    <tbody>



                      <tr style="background-color: #f8fafc; font-weight: bold; border-bottom: 1px solid #000;">



                        <td style="padding: 3px 6px; width: 18%; border: 1px solid #000;">Organisasi / Unit:</td>



                        <td style="padding: 3px 6px; width: 32%; font-weight: 900; border: 1px solid #000; text-transform: uppercase;">${act.org_name || '-'} [${act.org_category || ''}]</td>



                        <td style="padding: 3px 6px; width: 18%; border: 1px solid #000;">Tarikh & Hari:</td>



                        <td style="padding: 3px 6px; width: 32%; font-weight: bold; border: 1px solid #000;">${act.activity_date || '-'}</td>



                      </tr>



                      <tr style="border-bottom: 1px solid #000;">



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Tajuk Aktiviti:</td>



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">${act.title || '-'}</td>



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Masa & Tempat:</td>



                        <td style="padding: 3px 6px; border: 1px solid #000;">${act.start_time || '14:00'} - ${act.end_time || '16:00'} | ${act.venue || 'Sekolah'}</td>



                      </tr>



                      <tr>



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Guru Bertugas:</td>



                        <td style="padding: 3px 6px; border: 1px solid #000;">${act.teachers_involved || '-'}</td>



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000;">Status Laporan:</td>



                        <td style="padding: 3px 6px; font-weight: bold; border: 1px solid #000; color: ${act.status === 'Disahkan' ? '#047857' : '#1d4ed8'};">${act.status || 'Draf'}</td>



                      </tr>



                    </tbody>



                  </table>







                  <!-- Objektif & Perjalanan Aktiviti Side-by-Side -->



                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px; font-size: 8pt; line-height: 1.35;">



                    <div style="padding: 5px 7px; background-color: #f8fafc; border: 1px solid #000; border-radius: 4px;">



                      <div style="font-weight: 900; text-transform: uppercase; margin-bottom: 2px; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;">Objektif & Hasil Pembelajaran</div>



                      <div style="white-space: pre-line;">${act.objectives || 'Tiada objektif dinyatakan.'}</div>



                    </div>



                    <div style="padding: 5px 7px; background-color: #f8fafc; border: 1px solid #000; border-radius: 4px;">



                      <div style="font-weight: 900; text-transform: uppercase; margin-bottom: 2px; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px;">Ringkasan Perjalanan Aktiviti</div>



                      <div style="white-space: pre-line;">${act.description_rundown || 'Tiada butiran perjalanan aktiviti dinyatakan.'}</div>



                    </div>



                  </div>







                  <!-- Analisis & Rekod Kehadiran Murid (Hadir & Tidak Hadir) -->



                  <div style="border: 1px solid #000; border-radius: 4px; padding: 5px 7px; margin-bottom: 6px; background-color: #ffffff;">



                    <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; margin-bottom: 4px;">



                      <span style="font-weight: 900; font-size: 8.2pt; text-transform: uppercase;">Analisis & Rekod Kehadiran Murid</span>



                      <span style="font-size: 8pt; font-weight: bold;">



                        Jumlah: ${act.total_enrolled || (act.present_count + act.absent_count) || 0} | 



                        Hadir: <strong style="color: #047857;">${act.present_count || act.attendees_count || 0}</strong> | 



                        Tidak Hadir: <strong style="color: #b91c1c;">${act.absent_count || 0}</strong> | 



                        Peratusan: <strong style="color: #1d4ed8;">${act.percentage || 0}%</strong>



                      </span>



                    </div>







                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 7.8pt;">



                      <!-- Jadual Murid Hadir -->



                      <div style="border: 1px solid #059669; border-radius: 4px; overflow: hidden;">



                        <div style="background-color: #d1fae5; color: #065f46; font-weight: bold; padding: 2px 4px; text-align: center; text-transform: uppercase; font-size: 7.5pt;">



                          ✓ Senarai Murid Hadir (${act.present_students ? act.present_students.length : (act.attendees_count || 0)} orang)



                        </div>



                        <div style="padding: 4px; max-height: 110px; overflow-y: auto; line-height: 1.3;">



                          ${act.present_students && act.present_students.length > 0 ? `



                            <ol style="margin: 0; padding-left: 16px;">



                              ${act.present_students.map(name => `<li style="font-weight: 600;">${name}</li>`).join("")}



                            </ol>



                          ` : `<div style="color: #94a3b8; font-style: italic; text-align: center;">Tiada data nama murid hadir.</div>`}



                        </div>



                      </div>







                      <!-- Jadual Murid Tidak Hadir -->



                      <div style="border: 1px solid #e11d48; border-radius: 4px; overflow: hidden;">



                        <div style="background-color: #ffe4e6; color: #9f1239; font-weight: bold; padding: 2px 4px; text-align: center; text-transform: uppercase; font-size: 7.5pt;">



                          ✗ Senarai Murid Tidak Hadir (${act.absent_students ? act.absent_students.length : 0} orang)



                        </div>



                        <div style="padding: 4px; max-height: 110px; overflow-y: auto; line-height: 1.3;">



                          ${act.absent_students && act.absent_students.length > 0 ? `



                            <ol style="margin: 0; padding-left: 16px;">



                              ${act.absent_students.map(name => `<li style="color: #881337; font-weight: 600;">${name}</li>`).join("")}



                            </ol>



                          ` : `<div style="color: #047857; font-weight: bold; text-align: center; padding-top: 4px;">Semua ahli hadir (Tiada tidak hadir).</div>`}



                        </div>



                      </div>



                    </div>



                  </div>







                  <!-- Refleksi & Cadangan -->



                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 7.8pt; line-height: 1.3; margin-bottom: 6px;">



                    <div style="padding: 4px 6px; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px;">



                      <span style="font-weight: bold; display: block; margin-bottom: 1px;">Refleksi / Rumusan Guru:</span>



                      <div>${act.reflection || 'Aktiviti berjalan lancar mengikut perancangan.'}</div>



                    </div>



                    <div style="padding: 4px 6px; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 4px;">



                      <span style="font-weight: bold; display: block; margin-bottom: 1px;">Cadangan Penambahbaikan:</span>



                      <div>${act.suggestions || 'Teruskan latihan dan galakkan kehadiran penuh.'}</div>



                    </div>



                  </div>







                  <!-- Dokumentasi Gambar Jika Ada -->



                  ${[act.photo_1, act.photo_2, act.photo_3, act.photo_4].filter(Boolean).length > 0 ? `



                    <div style="border: 1px solid #cbd5e1; padding: 4px 6px; border-radius: 4px; margin-bottom: 4px;">



                      <span style="font-weight: bold; font-size: 7.5pt; display: block; margin-bottom: 2px;">Dokumentasi Gambar Aktiviti:</span>



                      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px;">



                        ${[act.photo_1, act.photo_2, act.photo_3, act.photo_4].filter(Boolean).map(url => `



                          <img src="${url}" style="width: 100%; height: 46px; object-fit: cover; border-radius: 3px; border: 1px solid #cbd5e1;" alt="Dokumentasi">



                        `).join("")}



                      </div>



                    </div>



                  ` : ''}



                </div>







                <!-- Ruangan Tandatangan Pengesahan Bawah (1 Page Fixed Fit) -->



                <div class="signature-section" style="display: flex; justify-content: space-between; border-top: 1px solid #000; padding-top: 6px; margin-top: 2px; font-size: 8pt;">



                  <div style="text-align: center; width: 170px;">



                    <div style="font-size: 7.5pt; color: #475569; margin-bottom: 22px;">Disediakan oleh:</div>



                    <div style="border-bottom: 1px solid #000;"></div>



                    <div style="font-weight: bold; text-transform: uppercase; margin-top: 2px;">${act.teachers_involved ? act.teachers_involved.split('&')[0].trim() : (school.su_koko_name || 'Guru Penasihat')}</div>



                    <div style="font-size: 7pt; color: #475569;">Guru Bertugas / Penasihat</div>



                  </div>







                  <div style="text-align: center; width: 170px;">



                    <div style="font-size: 7.5pt; color: #475569; margin-bottom: 22px;">Disahkan oleh:</div>



                    <div style="border-bottom: 1px solid #000;"></div>



                    <div style="font-weight: bold; text-transform: uppercase; margin-top: 2px;">${school.gpk_koko_name || 'GPK Kokurikulum'}</div>



                    <div style="font-size: 7pt; color: #475569;">Guru Penolong Kanan Kokurikulum</div>



                  </div>



                </div>



              </div>



            `).join("")}



          </div>



        `;



      }



    }



    // 2. Standard Table & Other Reports



    else {



      html = `



        <div class="bg-white text-black p-6 sm:p-9 rounded-xl shadow-2xl border border-slate-300 w-full max-w-4xl print:p-0 print:border-none print:shadow-none print:rounded-none">



          <!-- Official Letterhead (Left Logo, Right Address) -->



          ${this.generateLetterheadHTML(school, report.title, now)}



      `;







      if (Array.isArray(report.data)) {



        let headersHtml = "";



        let rowsHtml = "";







        if (rType === "filtered_students" || rType === "students_by_class" || rType === "students_by_sport_house") {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh Murid</th>



              <th>No. KP / MyKid</th>



              <th class="text-center">Jantina</th>



              <th>Kelas</th>



              <th>Rumah Sukan</th>



              <th>Unit Beruniform</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.full_name || '-'}</td>



              <td class="font-mono text-center">${r.ic_number || '-'}</td>



              <td class="text-center">${r.gender || '-'}</td>



              <td>${r.class_name || '-'}</td>



              <td>${r.sport_house_name || '-'}</td>



              <td>${r.uniform_unit_name || '-'}</td>



            </tr>



          `).join("");



        } else if (rType === "members_by_org") {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh Murid</th>



              <th>No. KP / MyKid</th>



              <th class="text-center">Kelas</th>



              <th>Jawatan AJK</th>



              <th>Nama Penjaga & No. Tel</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.full_name || '-'}</td>



              <td class="font-mono text-center">${r.ic_number || '-'}</td>



              <td class="text-center">${r.class_name || '-'}</td>



              <td><span class="font-semibold ${r.committee_position ? 'text-blue-900 font-bold' : ''}">${r.committee_position || 'Ahli Biasa'}</span></td>



              <td>${r.guardian_name || '-'} (${r.guardian_phone || '-'})</td>



            </tr>



          `).join("");



        } else if (rType === "student_committees") {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh Murid</th>



              <th>Jawatan Disandang</th>



              <th>Organisasi</th>



              <th>Kategori</th>



              <th class="text-center">Kelas</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.student_name || r.full_name || '-'}</td>



              <td class="font-bold text-navy-900">${r.position || '-'}</td>



              <td>${r.org_name || '-'}</td>



              <td>${r.org_category || '-'}</td>



              <td class="text-center">${r.class_name || '-'}</td>



            </tr>



          `).join("");



        } else if (rType === "student_achievements") {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh Murid</th>



              <th class="text-center">Kelas</th>



              <th>Nama Pertandingan / Program</th>



              <th class="text-center">Peringkat</th>



              <th class="text-center">Pencapaian</th>



              <th class="text-center">Skor PAJSK</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.student_name || '-'}</td>



              <td class="text-center">${r.class_name || '-'}</td>



              <td>${r.program_name || '-'}</td>



              <td class="text-center font-semibold">${r.participation_level || '-'}</td>



              <td class="text-center font-bold text-emerald-800">${r.achievement || '-'}</td>



              <td class="text-center font-black text-navy-900">${r.pajsk_score || 0}m</td>



            </tr>



          `).join("");



        } else if (rType === "pajsk_summary_class_or_org") {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh Murid</th>



              <th>No. KP / MyKid</th>



              <th class="text-center">Kelas</th>



              <th class="text-center">Jantina</th>



              <th class="text-center">Skor PAJSK</th>



              <th class="text-center">Gred</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.full_name || '-'}</td>



              <td class="font-mono text-center">${r.ic_number || '-'}</td>



              <td class="text-center">${r.class_name || '-'}</td>



              <td class="text-center">${r.gender || '-'}</td>



              <td class="text-center font-black text-navy-900">${r.total_pajsk || 0}m</td>



              <td class="text-center font-bold text-emerald-800">${r.gred || '-'}</td>



            </tr>



          `).join("");



        } else {



          headersHtml = `



            <tr>



              <th class="w-8 text-center">Bil</th>



              <th>Nama Penuh / Keterangan</th>



              <th>No. KP / Tarikh</th>



              <th>Kelas / Kategori</th>



              <th>Catatan / Status</th>



            </tr>



          `;



          rowsHtml = report.data.map((r, i) => `



            <tr>



              <td class="text-center font-bold">${i + 1}</td>



              <td class="font-bold">${r.full_name || r.student_name || r.title || r.name || r.program_name || '-'}</td>



              <td>${r.ic_number || r.session_date || r.activity_date || r.event_date || r.month || '-'}</td>



              <td>${r.class_name || r.org_category || r.category || '-'}</td>



              <td>${r.committee_position || r.position || r.status || r.achievement || r.remarks || '-'}</td>



            </tr>



          `).join("");



        }







        html += `



          <div class="mb-3 text-[11px] font-semibold text-slate-600 flex justify-between items-center">



            <span>Jumlah Rekod: <strong>${report.data.length}</strong> orang / entiti</span>



          </div>



          <table class="print-table">



            <thead>${headersHtml}</thead>



            <tbody>${rowsHtml.length ? rowsHtml : '<tr><td colspan="7" class="text-center p-4">Tiada rekod data dijumpai.</td></tr>'}</tbody>



          </table>



        `;



      } else if (typeof report.data === "object") {



        html += `



          <div class="space-y-4 my-4">



            <div class="p-3 bg-slate-50 border border-slate-300 rounded-lg">



              <h4 class="font-bold text-xs uppercase mb-1">Keputusan Pentaksiran Kokurikulum (PAJSK)</h4>



              <p class="text-[11px]">Murid ini telah menyertai aktiviti teras kokurikulum dan menunjukkan penglibatan yang aktif.</p>



            </div>



          </div>



        `;



      }







      // Official Signature Section



      html += `



          <div class="signature-section" style="margin-top: 24px;">



            <div class="text-center w-48">



              <div class="text-[10px] text-slate-600 mb-12">Disediakan oleh:</div>



              <div class="border-b border-black"></div>



              <div class="font-bold text-[11px] uppercase mt-1">${school.su_koko_name || 'Setiausaha Kokurikulum'}</div>



              <div class="text-[9px] text-slate-500">Setiausaha Kokurikulum</div>



            </div>







            <div class="text-center w-48">



              <div class="text-[10px] text-slate-600 mb-12">Disahkan oleh:</div>



              <div class="border-b border-black"></div>



              <div class="font-bold text-[11px] uppercase mt-1">${school.gpk_koko_name || 'GPK Kokurikulum'}</div>



              <div class="text-[9px] text-slate-500">Guru Penolong Kanan Kokurikulum</div>



            </div>



          </div>



        </div>



      `;



    }







    doc.innerHTML = html;



    lucide.createIcons();



  },







  // ==========================================



  // VIEW 9: TETAPAN SISTEM



  // ==========================================



  populateSettingsForm() {



    if (!state.schoolSettings) return;



    const s = state.schoolSettings;



    const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };







    set("setting-school-name", s.school_name);



    set("setting-school-code", s.school_code);



    set("setting-school-address", s.address);



    set("setting-school-phone", s.phone);



    set("setting-school-email", s.email);



    set("setting-principal-name", s.principal_name);



    set("setting-gpk-koko-name", s.gpk_koko_name);



    set("setting-su-koko-name", s.su_koko_name);



    set("setting-letter-template", s.letter_template);







    // Also load users table for Admin / GPK / SU



    this.loadSettingsUsers();



  },







  async loadSettingsUsers() {



    const tbody = document.getElementById("settings-users-table-body");



    const pendingContainer = document.getElementById("settings-pending-approval-container");



    const pendingTbody = document.getElementById("settings-pending-users-table-body");



    const pendingBadge = document.getElementById("pending-approval-count-badge");



    if (!tbody) return;







    try {



      // 1. Fetch pending registrations for approval



      try {



        const pRes = await fetch("/api/auth/pending-users");



        if (pRes.ok && pendingContainer && pendingTbody) {



          const pendingUsers = await pRes.json();



          state.pendingUsersList = pendingUsers;



          if (pendingUsers && pendingUsers.length > 0) {



            pendingContainer.classList.remove("hidden");



            if (pendingBadge) pendingBadge.textContent = `${pendingUsers.length} Permohonan Menunggu`;



            pendingTbody.innerHTML = pendingUsers.map(u => `



              <tr class="hover:bg-amber-50/50 transition">



                <td class="p-2.5">



                  <div class="font-bold text-slate-900">${u.full_name}</div>



                  <div class="text-[10px] text-amber-800 font-semibold">Guru Penasihat</div>



                </td>



                <td class="p-2.5 font-mono font-bold text-slate-800">${u.username}</td>



                <td class="p-2.5 text-slate-600 text-[11px]">${u.phone || '-'}<br><span class="text-[10px] text-slate-400">${u.email || '-'}</span></td>



                <td class="p-2.5 text-slate-700">${u.assigned_category || 'Semua Unit'}</td>



                <td class="p-2.5 text-slate-500 text-[10px]">${u.created_at ? u.created_at.substring(0, 16).replace('T', ' ') : '-'}</td>



                <td class="p-2.5 text-center">



                  <div class="inline-flex items-center space-x-1.5">



                    <button onclick="app.approveUserRegistration(${u.id})" 



                      title="Luluskan Akaun Guru" 



                      class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs flex items-center space-x-1 shadow-xs transition cursor-pointer">



                      <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>



                      <span>Luluskan</span>



                    </button>



                    <button onclick="app.rejectUserRegistration(${u.id})" 



                      title="Tolak Permohonan" 



                      class="px-2 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold rounded-lg text-xs flex items-center space-x-1 transition cursor-pointer">



                      <i data-lucide="x-circle" class="w-3.5 h-3.5"></i>



                      <span>Tolak</span>



                    </button>



                  </div>



                </td>



              </tr>



            `).join("");



          } else {



            pendingContainer.classList.add("hidden");



          }



        }



      } catch (e) {



        console.error("Pending users check error:", e);



      }







      // 2. Fetch all registered users



      const res = await fetch("/api/auth/users");



      if (!res.ok) {



        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400">Pengurusan akaun guru terhad kepada Admin, GPK Kokurikulum, dan Setiausaha Kokurikulum sahaja.</td></tr>`;



        return;



      }



      const users = await res.json();



      state.usersList = users;







      if (users.length === 0) {



        tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-slate-400">Tiada akaun guru dijumpai.</td></tr>`;



        return;



      }







      const roleBadges = {



        "Admin": "bg-red-100 text-red-800 border-red-200",



        "GPK Kokurikulum": "bg-amber-100 text-amber-800 border-amber-200",



        "Setiausaha Kokurikulum": "bg-blue-100 text-blue-800 border-blue-200",



        "Penyelaras Kokurikulum": "bg-purple-100 text-purple-800 border-purple-200",



        "Guru Penasihat": "bg-emerald-100 text-emerald-800 border-emerald-200"



      };







      tbody.innerHTML = users.map(u => {



        const badgeClass = roleBadges[u.role] || "bg-slate-100 text-slate-800 border-slate-200";



        const isSelf = state.currentUser && state.currentUser.id === u.id;



        const isPending = u.approval_status === 'pending' || u.is_active === 0;



        



        return `



          <tr class="hover:bg-slate-50 transition">



            <td class="p-3">



              <div class="font-bold text-navy-950 flex items-center space-x-1.5">



                <span>${u.full_name}</span>



                ${isPending ? `<span class="px-1.5 py-0.2 rounded text-[9px] bg-amber-100 text-amber-800 font-bold border border-amber-300">Menunggu Kelulusan</span>` : ''}



              </div>



              <div class="text-[10px] text-slate-500">${u.email || '-'}</div>



            </td>



            <td class="p-3 font-mono font-bold text-slate-700">${u.username}</td>



            <td class="p-3">



              <span class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${badgeClass}">



                ${u.role}



              </span>



            </td>



            <td class="p-3 text-slate-600">${u.phone || '-'}</td>



            <td class="p-3 text-slate-600">${u.assigned_category || 'Semua Unit'}</td>



            <td class="p-3 text-center">



              <div class="inline-flex items-center space-x-1">



                ${isPending ? `



                  <button onclick="app.approveUserRegistration(${u.id})" 



                    title="Luluskan Akaun Guru" 



                    class="p-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-bold transition flex items-center space-x-1 shadow-2xs cursor-pointer">



                    <i data-lucide="check" class="w-3.5 h-3.5"></i>



                    <span class="hidden xl:inline">Luluskan</span>



                  </button>



                ` : `



                  <!-- Reset Password Button -->



                  <button onclick="app.resetUserPassword(${u.id})" 



                    title="Reset Kata Laluan ke Default (aba6038)"



                    class="p-1.5 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-lg text-xs font-bold transition flex items-center space-x-1 shadow-2xs cursor-pointer">



                    <i data-lucide="key-round" class="w-3.5 h-3.5"></i>



                    <span class="hidden xl:inline">Reset Kata Laluan</span>



                  </button>



                `}



                



                <!-- Edit User Button -->



                <button onclick="app.openEditUserModal(${u.id})" 



                  title="Kemaskini Maklumat Guru"



                  class="p-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-bold transition shadow-2xs cursor-pointer">



                  <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>



                </button>







                <!-- Delete User Button (Hidden for Self) -->



                ${!isSelf ? `



                  <button onclick="app.deleteUser(${u.id})" 



                    title="Padam Akaun"



                    class="p-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-bold transition shadow-2xs cursor-pointer">



                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>



                  </button>



                ` : ''}



              </div>



            </td>



          </tr>



        `;



      }).join("");







      lucide.createIcons();



    } catch (err) {



      console.error(err);



      tbody.innerHTML = `<tr><td colspan="6" class="p-4 text-center text-rose-500">Ralat memuatkan senarai pengguna.</td></tr>`;



    }



  },







  async approveUserRegistration(userId, userName) {



    const confirm = await Swal.fire({



      title: 'Luluskan Pendaftaran Guru?',



      html: `Adakah anda pasti mahu mengesahkan & meluluskan akaun guru <b>${userName}</b>?<br><br>Guru ini akan dapat log masuk ke dalam sistem kokurikulum serta-merta.`,



      icon: 'question',



      showCancelButton: true,



      confirmButtonColor: '#16a34a',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Sahkan & Luluskan',



      cancelButtonText: 'Batal'



    });







    if (confirm.isConfirmed) {



      try {



        const res = await fetch(`/api/auth/users/${userId}/approve`, { method: "POST" });



        const data = await res.json();



        if (res.ok) {



          Swal.fire({



            icon: 'success',



            title: 'Akaun Diluluskan',



            text: data.message || 'Akaun guru telah berjaya disahkan dan diaktifkan.',



            timer: 2000,



            showConfirmButton: false



          });



          await this.loadSettingsUsers();



          await this.fetchTeachers();



        } else {



          Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal meluluskan akaun.' });



        }



      } catch (err) {



        console.error(err);



        Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa meluluskan akaun.' });



      }



    }



  },







  async rejectUserRegistration(userId, userName) {



    const confirm = await Swal.fire({



      title: 'Tolak Permohonan Guru?',



      html: `Adakah anda pasti mahu menolak permohonan akaun untuk <b>${userName}</b>? Rekod pendaftaran ini akan dipadam.`,



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#e11d48',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Tolak Permohonan',



      cancelButtonText: 'Batal'



    });







    if (confirm.isConfirmed) {



      try {



        const res = await fetch(`/api/auth/users/${userId}/reject`, { method: "POST" });



        const data = await res.json();



        if (res.ok) {



          Swal.fire({



            icon: 'info',



            title: 'Permohonan Ditolak',



            text: data.message || 'Permohonan pendaftaran akaun telah ditolak.',



            timer: 2000,



            showConfirmButton: false



          });



          await this.loadSettingsUsers();



        } else {



          Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal menolak permohonan.' });



        }



      } catch (err) {



        console.error(err);



        Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa menolak permohonan.' });



      }



    }



  },







  openRegisterTeacherModal() {



    const form = document.getElementById("form-user");



    if (form) form.reset();



    



    const idEl = document.getElementById("user-form-id");



    if (idEl) idEl.value = "";



    



    const pwdEl = document.getElementById("user-form-password");



    if (pwdEl) pwdEl.value = "aba6038";







    const titleEl = document.getElementById("modal-user-title");



    if (titleEl) titleEl.textContent = "Daftar Guru / Pengguna Baharu";







    const btnTextEl = document.getElementById("btn-save-user-text");



    if (btnTextEl) btnTextEl.textContent = "Simpan & Daftar Guru";







    this.openModal("modal-user");



  },







  openEditUserModal(userId) {



    const user = state.usersList ? state.usersList.find(u => u.id === userId) : null;



    if (!user) return;







    const idEl = document.getElementById("user-form-id");



    if (idEl) idEl.value = user.id;







    const nameEl = document.getElementById("user-form-fullname");



    if (nameEl) nameEl.value = user.full_name || "";







    const userEl = document.getElementById("user-form-username");



    if (userEl) userEl.value = user.username || "";







    const roleEl = document.getElementById("user-form-role");



    if (roleEl) roleEl.value = user.role || "Guru Penasihat";







    const emailEl = document.getElementById("user-form-email");



    if (emailEl) emailEl.value = user.email || "";







    const phoneEl = document.getElementById("user-form-phone");



    if (phoneEl) phoneEl.value = user.phone || "";







    const catEl = document.getElementById("user-form-category");



    if (catEl) catEl.value = user.assigned_category || "";







    const pwdEl = document.getElementById("user-form-password");



    if (pwdEl) pwdEl.value = "";







    const titleEl = document.getElementById("modal-user-title");



    if (titleEl) titleEl.textContent = "Kemaskini Maklumat Guru / Pengguna";







    const btnTextEl = document.getElementById("btn-save-user-text");



    if (btnTextEl) btnTextEl.textContent = "Kemaskini Maklumat";







    this.openModal("modal-user");



  },







  async handleSaveUserForm(e) {



    if (e) e.preventDefault();



    const id = document.getElementById("user-form-id")?.value;



    const fullName = document.getElementById("user-form-fullname")?.value.trim();



    const username = document.getElementById("user-form-username")?.value.trim();



    const role = document.getElementById("user-form-role")?.value;



    const email = document.getElementById("user-form-email")?.value.trim();



    const phone = document.getElementById("user-form-phone")?.value.trim();



    const category = document.getElementById("user-form-category")?.value;



    const password = document.getElementById("user-form-password")?.value.trim();







    if (!fullName || !username || !role) {



      Swal.fire({ icon: 'warning', title: 'Perhatian', text: 'Sila lengkapkan nama guru, username dan peranan.' });



      return;



    }







    try {



      let res;



      if (id) {



        const payload = {



          full_name: fullName,



          role: role,



          email: email || null,



          phone: phone || null,



          assigned_category: category || null



        };



        if (password) payload.password = password;







        res = await fetch(`/api/auth/users/${id}`, {



          method: "PUT",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      } else {



        const payload = {



          username: username,



          password: password || "aba6038",



          full_name: fullName,



          role: role,



          email: email || null,



          phone: phone || null,



          assigned_category: category || null



        };







        res = await fetch("/api/auth/users", {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify(payload)



        });



      }







      const data = await res.json();



      if (!res.ok) {



        Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal menyimpan maklumat pengguna.' });



        return;



      }







      this.closeModal("modal-user");



      Swal.fire({



        icon: 'success',



        title: 'Berjaya',



        text: data.message || 'Maklumat guru berjaya disimpan!',



        timer: 2000,



        showConfirmButton: false



      });







      await this.fetchTeachers();



      await this.loadSettingsUsers();



    } catch (err) {



      console.error(err);



      Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa menyimpan maklumat guru.' });



    }



  },







  async resetUserPassword(userId, userName = null) {



    if (!userName) {



      const u = state.usersList?.find(x => x.id === userId);



      userName = u ? u.full_name : 'Pengguna';



    }







    const confirm = await Swal.fire({



      title: 'Reset Kata Laluan?',



      html: `Adakah anda pasti mahu menetapkan semula kata laluan bagi <b>${userName}</b> kepada kata laluan lalai <b>aba6038</b>?`,



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#d97706',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Reset ke aba6038',



      cancelButtonText: 'Batal'



    });







    if (confirm.isConfirmed) {



      try {



        const res = await fetch(`/api/auth/users/${userId}/reset-password`, {



          method: "POST",



          headers: { "Content-Type": "application/json" },



          body: JSON.stringify({ new_password: "aba6038" })



        });



        const data = await res.json();



        if (res.ok) {



          Swal.fire({



            icon: 'success',



            title: 'Kata Laluan Diset Semula',



            html: `Kata laluan untuk <b>${userName}</b> telah berjaya diset semula kepada <b>aba6038</b>.`,



            confirmButtonColor: '#1e3a8a'



          });



        } else {



          Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal menetapkan semula kata laluan.' });



        }



      } catch (err) {



        console.error(err);



        Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa menetapkan semula kata laluan.' });



      }



    }



  },







  async deleteUser(userId, userName = null) {



    if (!userName) {



      const u = state.usersList?.find(x => x.id === userId);



      userName = u ? u.full_name : 'Pengguna';



    }







    const confirm = await Swal.fire({



      title: 'Padam Akaun Pengguna?',



      html: `Adakah anda pasti untuk memadam akaun guru <b>${userName}</b>? Tindakan ini tidak boleh diundur.`,



      icon: 'error',



      showCancelButton: true,



      confirmButtonColor: '#e11d48',



      cancelButtonColor: '#64748b',



      confirmButtonText: 'Ya, Padam Akaun',



      cancelButtonText: 'Batal'



    });







    if (confirm.isConfirmed) {



      try {



        const res = await fetch(`/api/auth/users/${userId}`, { method: "DELETE" });



        const data = await res.json();



        if (res.ok) {



          Swal.fire({ icon: 'success', title: 'Akaun Dipadam', text: data.message || 'Akaun pengguna telah dipadam.', timer: 1500, showConfirmButton: false });



          await this.loadSettingsUsers();



          await this.fetchTeachers();



        } else {



          Swal.fire({ icon: 'error', title: 'Ralat', text: data.detail || 'Gagal memadam akaun pengguna.' });



        }



      } catch (err) {



        console.error(err);



        Swal.fire({ icon: 'error', title: 'Ralat', text: 'Ralat rangkaian semasa memadam pengguna.' });



      }



    }



  },







  async saveSchoolSettings(e) {



    e.preventDefault();



    const payload = {



      school_name: document.getElementById("setting-school-name").value.trim(),



      school_code: document.getElementById("setting-school-code").value.trim(),



      address: document.getElementById("setting-school-address").value.trim(),



      phone: document.getElementById("setting-school-phone").value.trim(),



      email: document.getElementById("setting-school-email").value.trim(),



      principal_name: document.getElementById("setting-principal-name").value.trim(),



      gpk_koko_name: document.getElementById("setting-gpk-koko-name").value.trim(),



      su_koko_name: document.getElementById("setting-su-koko-name").value.trim(),



      letter_template: document.getElementById("setting-letter-template").value.trim()



    };







    try {



      const res = await fetch("/api/settings/school", {



        method: "PUT",



        headers: { "Content-Type": "application/json" },



        body: JSON.stringify(payload)



      });







      if (res.ok) {



        Swal.fire({ icon: 'success', title: 'Berjaya', text: 'Maklumat sekolah berjaya dikemas kini!', timer: 2000, showConfirmButton: false });



        await this.fetchSchoolSettings();



      }



    } catch (err) {



      console.error(err);



    }



  },







  async resetDemoData() {



    const res = await Swal.fire({



      title: 'Set Semula Pangkalan Data?',



      text: 'Semua data akan diset semula kepada data demonstrasi lengkap SK Sungai Dendang.',



      icon: 'warning',



      showCancelButton: true,



      confirmButtonColor: '#16a34a',



      confirmButtonText: 'Ya, Set Semula'



    });







    if (res.isConfirmed) {



      try {



        Swal.fire({ title: 'Sedang Memproses...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });



        const response = await fetch("/api/settings/reset-demo", { method: "POST" });



        if (response.ok) {



          Swal.fire({ icon: 'success', title: 'Berjaya', text: 'Pangkalan data telah berjaya diset semula!' });



          await this.init();



        }



      } catch (e) {



        console.error(e);



      }



    }



  },







  async uploadLogo(input) {



    if (!input.files || input.files.length === 0) return;



    const formData = new FormData();



    formData.append("file", input.files[0]);







    try {



      const res = await fetch("/api/settings/upload-logo", { method: "POST", body: formData });



      if (res.ok) {



        Swal.fire({ icon: 'success', title: 'Logo Dikemaskini', timer: 1500, showConfirmButton: false });



        await this.fetchSchoolSettings();



      }



    } catch (e) {



      console.error(e);



    }



  },







  // Helper: Modal opener



  openModal(modalId) {



    const modal = document.getElementById(modalId);



    if (modal) {



      modal.classList.remove("hidden");



      lucide.createIcons();



    }



  },







  // Helper: Modal closer



  closeModal(modalId) {



    const modal = document.getElementById(modalId);



    if (modal) modal.classList.add("hidden");



  }



};







// Start application on DOM Ready



document.addEventListener("DOMContentLoaded", () => {



  app.init();



});















// Intercept Ctrl+P / Cmd+P to use isolated iframe printing for modals



window.addEventListener("keydown", (e) => {



  if ((e.ctrlKey || e.metaKey) && (e.key === "p" || e.key === "P")) {



    const modal = document.getElementById("modal-print-preview");



    if (modal && !modal.classList.contains("hidden")) {



      e.preventDefault();



      app.printCurrentDocument();



    }



  }



});



