// i18n: English, Arabic (RTL), French

export const LANGS = ["en", "ar", "fr"];

const dict = {
  en: {
    app: "Oasis",
    tagline: "Smart Desert Orchard Management",
    login: "Sign in",
    email: "Email",
    password: "Password",
    demo: "Use demo account",
    logout: "Sign out",
    nav_dashboard: "Dashboard",
    nav_map: "Farm Map",
    nav_irrigation: "Irrigation",
    nav_soil: "Soil & Salinity",
    nav_water: "Water",
    nav_health: "Crop Health",
    nav_diagnosis: "AI Diagnosis",
    nav_fertigation: "Fertilization",
    nav_climate: "Climate Risks",
    nav_tasks: "Tasks",
    nav_sensors: "Sensors",
    nav_reports: "Reports",
    nav_variety: "Variety Selector",
    nav_algeria: "Algeria · Planting",
    nav_alerts: "Alert Center",
    today_priorities: "Today's Priorities",
    add: "Add",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    confidence: "Confidence",
    assumptions: "Assumptions",
    actions: "Actions",
    status: "Status",
    zone: "Zone",
    loading: "Loading…",
    none: "None",
  },
  ar: {
    app: "الواحة",
    tagline: "إدارة البساتين الذكية في المناطق الصحراوية",
    login: "تسجيل الدخول",
    email: "البريد الإلكتروني",
    password: "كلمة المرور",
    demo: "استخدام الحساب التجريبي",
    logout: "تسجيل الخروج",
    nav_dashboard: "لوحة المتابعة",
    nav_map: "خريطة المزرعة",
    nav_irrigation: "الري",
    nav_soil: "التربة والملوحة",
    nav_water: "المياه",
    nav_health: "صحة المحصول",
    nav_diagnosis: "التشخيص بالذكاء الاصطناعي",
    nav_fertigation: "التسميد",
    nav_climate: "المخاطر المناخية",
    nav_tasks: "المهام",
    nav_sensors: "أجهزة الاستشعار",
    nav_reports: "التقارير",
    nav_variety: "اختيار الأصناف",
    nav_algeria: "الجزائر · الزراعة",
    nav_alerts: "مركز التنبيهات",
    today_priorities: "أولويات اليوم",
    add: "إضافة",
    save: "حفظ",
    cancel: "إلغاء",
    delete: "حذف",
    confidence: "درجة الثقة",
    assumptions: "الافتراضات",
    actions: "الإجراءات",
    status: "الحالة",
    zone: "المنطقة",
    loading: "جارٍ التحميل…",
    none: "لا يوجد",
  },
  fr: {
    app: "Oasis",
    tagline: "Gestion intelligente des vergers désertiques",
    login: "Connexion",
    email: "E-mail",
    password: "Mot de passe",
    demo: "Utiliser le compte démo",
    logout: "Déconnexion",
    nav_dashboard: "Tableau de bord",
    nav_map: "Carte de la ferme",
    nav_irrigation: "Irrigation",
    nav_soil: "Sol et salinité",
    nav_water: "Eau",
    nav_health: "Santé des cultures",
    nav_diagnosis: "Diagnostic IA",
    nav_fertigation: "Fertilisation",
    nav_climate: "Risques climatiques",
    nav_tasks: "Tâches",
    nav_sensors: "Capteurs",
    nav_reports: "Rapports",
    nav_variety: "Sélection de variétés",
    nav_algeria: "Algérie · Plantation",
    nav_alerts: "Centre d'alertes",
    today_priorities: "Priorités du jour",
    add: "Ajouter",
    save: "Enregistrer",
    cancel: "Annuler",
    delete: "Supprimer",
    confidence: "Confiance",
    assumptions: "Hypothèses",
    actions: "Actions",
    status: "Statut",
    zone: "Zone",
    loading: "Chargement…",
    none: "Aucun",
  },
};

let current = "en";

export function setLang(lang) {
  current = dict[lang] ? lang : "en";
  document.documentElement.lang = current;
  document.documentElement.dir = current === "ar" ? "rtl" : "ltr";
  const btn = document.getElementById("lang-btn");
  if (btn) btn.textContent = "🌐 " + current.toUpperCase();
  localStorage.setItem("oasis_lang", current);
}

export function initLang() {
  const saved = localStorage.getItem("oasis_lang");
  setLang(saved && dict[saved] ? saved : "en");
}

export function t(key, vars = {}) {
  let s = dict[current][key] ?? dict.en[key] ?? key;
  for (const [k, v] of Object.entries(vars)) {
    s = s.replaceAll("{" + k + "}", String(v));
  }
  return s;
}