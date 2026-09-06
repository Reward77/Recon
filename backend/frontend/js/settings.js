/* global api, protectPage */
(function () {
  const $ = (id) => document.getElementById(id);
  const form = $("settingsForm");
  const message = $("settingsMessage");
  function setMessage(text, isError) { message.textContent = text; message.classList.toggle("is-error", Boolean(isError)); }
  function setForm(data) {
    $("companyName").value = data.company_name || ""; $("companyEmail").value = data.company_email || "";
    $("companyPhone").value = data.phone || ""; $("companyAddress").value = data.address || "";
    const p = data.preferences || {};
    $("currency").value = p.currency || "NGN"; $("dateFormat").value = p.date_format || "DD/MM/YYYY";
    $("amountTolerance").value = p.amount_tolerance || "0.00"; $("autoMatch").checked = p.auto_match !== false;
    $("emailNotifications").checked = p.email_notifications !== false; $("exceptionNotifications").checked = p.exception_notifications !== false;
  }
  async function load() { setForm(await api("/settings")); }
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); const button = form.querySelector("button[type=submit]"); button.disabled = true; setMessage("Saving settings…");
    const payload = { company_name: $("companyName").value, company_email: $("companyEmail").value, phone: $("companyPhone").value, address: $("companyAddress").value, preferences: { currency: $("currency").value, date_format: $("dateFormat").value, amount_tolerance: $("amountTolerance").value, auto_match: $("autoMatch").checked, email_notifications: $("emailNotifications").checked, exception_notifications: $("exceptionNotifications").checked } };
    try { setForm(await api("/settings", "PUT", payload)); setMessage("Settings saved."); } catch (error) { setMessage(error.message, true); } finally { button.disabled = false; }
  });
  window.addEventListener("DOMContentLoaded", async () => { protectPage(); try { await load(); } catch (error) { setMessage(error.message, true); } });
}());
