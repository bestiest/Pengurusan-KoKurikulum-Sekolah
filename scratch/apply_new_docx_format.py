import re

# 1. Update app/static/js/app.js
with open("app/static/js/app.js", "r", encoding="utf-8") as f:
    js_text = f.read()

# Add renderParentConsentDocxSlip
slip_func = """
  renderParentConsentDocxSlip(st, letter, school, isCopy = false) {
    const schoolName = (school && school.school_name) ? school.school_name : "SK TOH RAKNA SAKTI";
    const schoolAddress = (school && school.address) ? school.address : "34140 RANTAU PANJANG, SELAMA, PERAK DR.";

    let addrLine1 = "34140 RANTAU PANJANG";
    let addrLine2 = "SELAMA, PERAK DR.";
    if (schoolAddress.includes(",")) {
      const parts = schoolAddress.split(",");
      addrLine1 = parts[0].trim();
      addrLine2 = parts.slice(1).join(", ").trim();
    }

    const schoolPhone = (school && school.phone) ? school.phone : "05-8392473";
    const schoolFax = "05-8392473";
    const schoolEmail = (school && school.email) ? school.email : "ABA6044@1bestarinet.yes.my";

    let rawPrincipal = (school && school.principal_name) ? school.principal_name : "MOHD FIRUZ BIN ZAINUL";
    rawPrincipal = rawPrincipal.replace(/\\s*\\(.*?\\)\\s*/g, '').trim();

    const programName = (letter.program_name || "-").toUpperCase();
    const destination = (letter.destination_venue || "-").toUpperCase();

    const malayMonths = ["JANUARI", "FEBRUARI", "MAC", "APRIL", "MEI", "JUN", "JULAI", "OGOS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DISEMBER"];
    const malayDays = ["AHAD", "ISNIN", "SELASA", "RABU", "KHAMIS", "JUMAAT", "SABTU"];

    let tarikhProgram = "-";
    let masaHariProgram = "-";
    let tarikhSurat = new Date().toLocaleDateString("ms-MY", { day: "numeric", month: "numeric", year: "numeric" });

    if (letter.start_datetime) {
      try {
        const d1 = new Date(letter.start_datetime.replace(" ", "T"));
        if (!isNaN(d1.getTime())) {
          tarikhProgram = `${d1.getDate()} ${malayMonths[d1.getMonth()]} ${d1.getFullYear()}`;
          const dayName = malayDays[d1.getDay()];
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

    return `
      <div style="font-size: 7.2pt; line-height: 1.25; color: #000; display: flex; flex-direction: column; justify-content: space-between; height: 100%; box-sizing: border-box;">
        <!-- TOP: SURAT MAKLUMAN SEKOLAH -->
        <div>
          <!-- Title -->
          <div style="text-align: center; font-weight: bold; font-size: 8.5pt; text-transform: uppercase; margin-bottom: 2px; letter-spacing: 0.5px;">
            KEBENARAN IBU BAPA ${isCopy ? '<span style="font-size: 6.5pt; color: #475569; font-weight: normal; margin-left: 6px;">(SALINAN KEDUA)</span>' : ''}
          </div>

          <!-- School Letterhead -->
          <div style="display: flex; align-items: flex-start; justify-content: space-between; border-bottom: 1.5px solid #000; padding-bottom: 3px; margin-bottom: 5px;">
            <div style="width: 50px; min-width: 50px; text-align: left;">
              <img src="/static/images/school_logo.png?v=2" style="height: 48px; width: 48px; object-fit: contain;" alt="Logo">
            </div>
            <div style="flex: 1; padding-left: 6px; display: flex; justify-content: space-between; align-items: flex-start;">
              <div>
                <div style="font-size: 8pt; font-weight: bold; text-transform: uppercase;">${schoolName}</div>
                <div style="font-size: 6.5pt; font-weight: bold; text-transform: uppercase;">${addrLine1}</div>
                <div style="font-size: 6.5pt; font-weight: bold; text-transform: uppercase;">${addrLine2}</div>
              </div>
              <div style="text-align: right; font-size: 6pt; line-height: 1.25;">
                <div>NO.TEL : ${schoolPhone}</div>
                <div>NO. FAXS: ${schoolFax}</div>
                <div>Email : ${schoolEmail}</div>
                <div style="font-weight: bold; margin-top: 1px;">Tarikh : ${tarikhSurat}</div>
              </div>
            </div>
          </div>

          <!-- Salutation -->
          <div style="font-weight: bold; font-size: 7.5pt; margin-bottom: 2px;">Tuan, puan,</div>

          <!-- Body intro -->
          <div style="font-size: 6.8pt; text-align: justify; margin-bottom: 4px; line-height: 1.25;">
            Dengan sukacita dimaklumkan bahawa anak / jagaan tuan / puan yang bernama <span style="font-weight: bold; text-decoration: underline;">${st.student_name}</span> dari kelas <span style="font-weight: bold; text-decoration: underline;">${st.class_name || '-'}</span> telah terpilih untuk mengikuti aktiviti / program tersebut pada ketentuan berikut :
          </div>

          <!-- Table 1 -->
          <table style="width: 100%; border-collapse: collapse; margin-bottom: 4px; font-size: 6.8pt;">
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; width: 26%; background-color: #f8fafc;">AKTIVITI</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${programName}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">TARIKH</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${tarikhProgram}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">MASA / HARI</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${masaHariProgram}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">TEMPAT</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${destination}</td>
            </tr>
          </table>

          <!-- Paragraph 2 -->
          <div style="font-size: 6.6pt; text-align: justify; margin-bottom: 3px; line-height: 1.2;">
            2. &nbsp; Sehubungan dengan ini, pihak sekolah memohon tuan / puan melengkapkan borang kebenaran yang disertakan dan mengembalikannya dengan kadar yang segera.
          </div>

          <!-- Sign-off -->
          <div style="font-size: 6.6pt; line-height: 1.2; margin-top: 2px;">
            <div>Sekian, Terima Kasih</div>
            <div style="font-weight: bold; margin: 1px 0;">“BERKHIDMAT UNTUK NEGARA”</div>
            <div>Saya yang menurut perintah,</div>
            <div style="margin-top: 14px;">
              <div style="border-bottom: 1px dotted #000; width: 130px;"></div>
              <div style="font-weight: bold; text-transform: uppercase; margin-top: 2px; font-size: 6.5pt;">(${rawPrincipal})</div>
              <div style="font-size: 6pt; text-transform: uppercase;">GURU BESAR</div>
            </div>
          </div>
        </div>

        <!-- DIVIDER BETWEEN TOP & BOTTOM -->
        <div style="border-top: 1px dashed #000; margin: 6px 0 4px 0; padding-top: 2px;"></div>

        <!-- BOTTOM: BORANG KEBENARAN WARIS -->
        <div>
          <!-- Parent Statement -->
          <div style="font-size: 6.8pt; text-align: justify; margin-bottom: 4px; line-height: 1.25;">
            Saya <span style="font-weight: bold; text-decoration: underline;">${st.guardian_name ? st.guardian_name.toUpperCase() : '___________________________________________________'}</span> ibu bapa / penjaga membenarkan anak di bawah jagaan saya yang bernama <span style="font-weight: bold; text-decoration: underline;">${st.student_name}</span> Sijil Beranak / K.P. bernombor <span style="font-weight: bold; text-decoration: underline;">${st.ic_number || '______________________'}</span> untuk menyertai aktiviti tersebut seperti ketentuan di bawah ini. :
          </div>

          <!-- Table 2 -->
          <table style="width: 100%; border-collapse: collapse; margin-bottom: 4px; font-size: 6.8pt;">
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; width: 26%; background-color: #f8fafc;">AKTIVITI</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${programName}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">TARIKH</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${tarikhProgram}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">MASA / HARI</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${masaHariProgram}</td>
            </tr>
            <tr>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold; background-color: #f8fafc;">TEMPAT</td>
              <td style="border: 1px solid #000; padding: 2px 4px; font-weight: bold;">${destination}</td>
            </tr>
          </table>

          <!-- Clauses 2, 3, 4 -->
          <div style="font-size: 6.3pt; text-align: justify; line-height: 1.2;">
            <div style="margin-bottom: 2px;">
              2. &nbsp; Sehubungan dengan ini, saya ingin memaklumkan bahawa anak / jagaan saya adalah sihat, tiada masalah kesihatan dan boleh mengambil bahagian dalam aktiviti berkenaan. Saya juga mengakui bahawa anak saya dilindungi oleh Insuran Takaful.
            </div>
            <div style="margin-bottom: 2px;">
              3. &nbsp; Saya faham bahawa pihak sekolah dan penganjur akan memastikan segala langkah keselamatan yang perlu. Walau bagaimana pun, saya mengakui tidak akan mengambil sebarang tindakan mahkamah terhadap pihak penganjur atau guru pengiring / sekolah jika berlaku sebarang kemalangan, kematian, kecacatan anggota, kehilangan anggota atau sebarang kecederaan lain terhadap anak / jagaan saya sama ada didalam perjalanan pergi dan balik mahu pun sepanjang aktiviti tersebut.
            </div>
            <div style="margin-bottom: 3px;">
              4. &nbsp; Sehubungan dengan itu, saya juga membenarkan pihak sekolah dan penganjur untuk memberi sebarang rawatan yang perlu kepada anak / jagaan saya sekiranya didapati perlu oleh pihak yang berkenaan.
            </div>
          </div>

          <div style="font-size: 6.5pt; margin-bottom: 3px;">Sekian, terima kasih.</div>

          <!-- Sign details -->
          <div style="font-size: 6.4pt; line-height: 1.45;">
            <div style="display: flex; justify-content: space-between;">
              <div>Tandatangan ibu bapa / penjaga : _________________________</div>
              <div>Tarikh : _________________________</div>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <div>Nombor Kad Pengenalan : _________________________</div>
              <div>Tel. Bimbit : <span style="font-weight: bold;">${st.guardian_phone || '_____________'}</span></div>
            </div>
            <div>Alamat Rumah : <span style="font-weight: bold;">${st.address || '_______________________________________________________________'}</span></div>
          </div>
        </div>
      </div>
    `;
  },
"""

if "renderParentConsentDocxSlip(" not in js_text:
    js_text = js_text.replace("renderPermissionLetterPrintDocument(letter, format, studentScope) {", slip_func + "\n  renderPermissionLetterPrintDocument(letter, format, studentScope) {", 1)
    print("Added renderParentConsentDocxSlip!")

# Replace format === "health" block
q = chr(34)
start_tag = 'else if (format === ' + q + 'health' + q + ')'
end_tag = 'doc.innerHTML = html;'

idx_start = js_text.find(start_tag)
idx_end = js_text.find(end_tag, idx_start)

new_health_block = """else if (format === "health") {
      if (studentsToPrint.length === 0) {
        html = `<div class="p-8 text-center text-slate-500 bg-white border border-slate-300 rounded-xl my-4 shadow">Tiada murid dipilih untuk cetakan Surat Kebenaran.</div>`;
      } else {
        const pages = [];
        for (let i = 0; i < studentsToPrint.length; i += 2) {
          const stLeft = studentsToPrint[i];
          const stRight = (i + 1 < studentsToPrint.length) ? studentsToPrint[i + 1] : stLeft;
          const isRightDuplicate = (i + 1 >= studentsToPrint.length);
          pages.push({ stLeft, stRight, isRightDuplicate, pageNum: Math.floor(i / 2) + 1 });
        }

        html = `
          <div class="w-full flex flex-col items-center">
            ${pages.map((p, pIdx) => `
              ${pIdx > 0 ? `
                <div class="no-print my-6 flex items-center justify-center w-full max-w-4xl">
                  <div class="h-px bg-slate-400 flex-1"></div>
                  <span class="mx-4 px-4 py-1.5 bg-slate-800 text-white rounded-full text-xs font-bold shadow-md flex items-center space-x-1.5">
                    <i data-lucide="file-text" class="w-3.5 h-3.5 text-blue-400"></i>
                    <span>Helaian / Muka Surat ${p.pageNum} (A4 Landscape - 2 Salinan)</span>
                  </span>
                  <div class="h-px bg-slate-400 flex-1"></div>
                </div>
              ` : ''}

              <div class="landscape-sheet letter-parent-sheet bg-white text-black p-4 sm:p-5 rounded-xl shadow-2xl border border-slate-300 w-full max-w-[1050px] mb-8 print:w-full print:max-w-none print:m-0 print:p-0 print:border-none print:shadow-none print:rounded-none" style="page-break-after: always !important; break-after: page !important; box-sizing: border-box; font-family: Arial, Helvetica, sans-serif;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; position: relative;">
                  <!-- Dotted Cut Line in Center -->
                  <div class="no-print" style="position: absolute; left: 50%; top: 0; bottom: 0; width: 0; border-left: 1.5px dashed #94a3b8; pointer-events: none; z-index: 10;">
                    <span style="position: absolute; top: 48%; left: -8px; background: #fff; padding: 2px; font-size: 8pt; color: #64748b;">✂</span>
                  </div>
                  <!-- Print center cut line -->
                  <div class="print-only" style="position: absolute; left: 50%; top: 0; bottom: 0; width: 0; border-left: 1px dashed #000; pointer-events: none;"></div>

                  <!-- LEFT SLIP -->
                  <div style="padding-right: 10px; border-right: 1px dashed #e2e8f0;">
                    ${this.renderParentConsentDocxSlip(p.stLeft, letter, school, false)}
                  </div>

                  <!-- RIGHT SLIP -->
                  <div style="padding-left: 10px;">
                    ${this.renderParentConsentDocxSlip(p.stRight, letter, school, p.isRightDuplicate)}
                  </div>
                </div>
              </div>
            `).join("")}
          </div>
        `;
      }
    }

    """

if idx_start != -1 and idx_end != -1:
    js_text = js_text[:idx_start] + new_health_block + js_text[idx_end:]
    print("Replaced format === health block successfully!")

# Ensure printCurrentDocument recognizes letter-parent-sheet
if "letter-parent-sheet" not in js_text:
    js_text = js_text.replace(
        'container.querySelector(".table-landscape, .landscape-sheet")',
        'container.querySelector(".table-landscape, .landscape-sheet, .letter-parent-sheet")'
    )
    print("Updated printCurrentDocument for letter-parent-sheet!")

with open("app/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(js_text)
print("Updated app/static/js/app.js!")

# 2. Update app/templates/index.html
with open("app/templates/index.html", "r", encoding="utf-8") as f:
    html_text = f.read()

# Update option 3 label
old_opt3 = """                <span>3. Format Kebenaran Waris & Akuan Kesihatan</span>
                <span class="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[10px] font-bold">Kesihatan & Rawatan</span>
              </div>
              <div class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">Format gabungan kebenaran menyertai aktiviti berserta borang deklarasi/akuan kesihatan murid (asma, jantung, alahan makanan/ubat).</div>"""

new_opt3 = """                <span>3. Format Surat Kebenaran Ibu Bapa (Contoh Rasmi Docx)</span>
                <span class="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded text-[10px] font-bold">2 Salinan / A4 Landscape</span>
              </div>
              <div class="text-[11px] text-slate-600 mt-0.5 leading-relaxed">Format rasmi surat kebenaran ibu bapa / penjaga (2 salinan dalam 1 helaian A4 Landscape berserta pelepasan tanggungan & akuan takaful).</div>"""

if old_opt3 in html_text:
    html_text = html_text.replace(old_opt3, new_opt3, 1)
    print("Updated option 3 label in index.html!")

# Update cache buster to v=6.0
html_text = html_text.replace('app.js?v=5.9', 'app.js?v=6.0')
print("Bumped cache buster to v=6.0!")

with open("app/templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_text)
print("Updated index.html!")

# 3. Update app/static/css/custom.css
with open("app/static/css/custom.css", "r", encoding="utf-8") as f:
    css_text = f.read()

if ".letter-parent-sheet" not in css_text:
    sheet_css = """
/* Borang Surat Kebenaran Ibu Bapa (Format Rasmi Docx A4 Landscape 2-Salinan) */
.letter-parent-sheet {
  font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
  color: #000000;
  box-sizing: border-box;
  background-color: #ffffff;
}

@media print {
  .letter-parent-sheet {
    display: block !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    page-break-after: always !important;
    break-after: page !important;
    margin: 0 !important;
    padding: 6mm 8mm !important;
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 0 !important;
    background: #ffffff !important;
    box-sizing: border-box !important;
  }
  .letter-parent-sheet:last-child,
  .letter-parent-sheet:last-of-type {
    page-break-after: auto !important;
    break-after: auto !important;
  }
}
"""
    css_text += sheet_css
    with open("app/static/css/custom.css", "w", encoding="utf-8") as f:
        f.write(css_text)
    print("Updated custom.css!")
