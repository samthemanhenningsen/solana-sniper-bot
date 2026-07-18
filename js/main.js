/* ============================================================
   Psic. Luis Alberto Morales Pérez — site interactions
   Mobile nav · scroll reveal · back-to-top · ES/EN toggle
   ============================================================ */

(function () {
  "use strict";

  /* ---------- Mobile nav ---------- */
  const burger = document.getElementById("navBurger");
  const nav = document.getElementById("siteNav");

  burger.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    burger.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", String(open));
  });

  nav.querySelectorAll("a").forEach((link) =>
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      burger.classList.remove("open");
      burger.setAttribute("aria-expanded", "false");
    })
  );

  /* ---------- Scroll reveal ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in-view"));
  }

  /* ---------- Back to top ---------- */
  const backToTop = document.getElementById("backToTop");
  window.addEventListener(
    "scroll",
    () => backToTop.classList.toggle("visible", window.scrollY > 600),
    { passive: true }
  );
  backToTop.addEventListener("click", () =>
    window.scrollTo({ top: 0, behavior: "smooth" })
  );

  /* ---------- Footer year ---------- */
  document.getElementById("year").textContent = new Date().getFullYear();

  /* ---------- ES / EN language toggle ----------
     Spanish lives in the HTML. On first toggle we cache the Spanish
     strings from the DOM, then swap against the EN dictionary below. */

  const EN = {
    "brand.tag": "Psychologist · Mexicali",
    "nav.about": "About me",
    "nav.services": "Specialties",
    "nav.process": "How I work",
    "nav.faq": "FAQ",
    "nav.contact": "Contact",
    "nav.cta": "Book a consult",

    "hero.eyebrow": "Psychologist in Mexicali, B.C. · SEP professional license",
    "hero.title": "Regain your emotional balance and strengthen your relationships",
    "hero.lead":
      "There are stages in life when we need support: to care for our personal or couple relationships, rediscover our purpose, and feel at peace again. You don't have to go through them alone.",
    "hero.cta1": "Free 15-minute consultation",
    "hero.cta2": "Call: 800 283 2791",
    "hero.badge1": "✓ In-person and online sessions",
    "hero.badge2": "✓ Individual and couples therapy",
    "hero.badge3": "✓ A confidential, judgment-free space",

    "trust.1": "Free initial consultation",
    "trust.2num": "Online",
    "trust.2": "Video-call sessions available",
    "trust.3": "National Registry of Professionals",
    "trust.4": "Guaranteed confidentiality",

    "about.eyebrow": "About me",
    "about.title": "Luis Alberto Morales Pérez, Lic. in Psychology",
    "about.p1":
      "I hold a degree in Psychology and am registered with Mexico's National Registry of Professionals (SEP). I work with individuals and couples going through anxiety, stress, sadness, or disconnection who want to feel in charge of their lives again.",
    "about.p2":
      "My work focuses on helping you regulate anxiety and depression, strengthen your self-esteem, learn to set healthy boundaries, and build healthier couple relationships. I believe in therapy that is warm, practical, and built on trust.",
    "about.li1": "Warm, direct, judgment-free care",
    "about.li2": "Clear goals and measurable progress in your process",
    "about.li3": "Office in Mexicali plus online sessions from anywhere",
    "about.cta": "Take the first step today",

    "services.eyebrow": "Specialties",
    "services.title": "How can I support you?",
    "services.sub":
      "Every process is different. These are the areas I work with most often.",
    "services.c1t": "Anxiety & stress",
    "services.c1p":
      "Tools to calm your mind, regulate emotions, and get your rest back when worry won't let you move forward.",
    "services.c2t": "Depression & sadness",
    "services.c2p":
      "Support to move through deep sadness, reconnect with what matters to you, and recover your day-to-day energy.",
    "services.c3t": "Couples therapy",
    "services.c3p":
      "A neutral space to improve communication, heal wounds, and build a stronger, healthier relationship.",
    "services.c4t": "Self-esteem",
    "services.c4p":
      "Deep work to strengthen the way you see, speak to, and treat yourself — and leave constant self-criticism behind.",
    "services.c5t": "Healthy boundaries",
    "services.c5p":
      "Learn to say no without guilt, protect your time and energy, and relate to others from mutual respect.",
    "services.c6t": "Life purpose",
    "services.c6p":
      "When you feel you've lost your way, I'll help you find your direction again and make decisions with clarity.",

    "process.eyebrow": "How I work",
    "process.title": "A clear process, at your pace",
    "process.s1t": "Free initial consult",
    "process.s1p":
      "We talk for 15 minutes by phone, free and with no commitment, to understand your situation and answer your questions.",
    "process.s2t": "First session",
    "process.s2p":
      "We explore in depth what you're going through and define the goals of your therapeutic process together.",
    "process.s3t": "Therapeutic process",
    "process.s3p":
      "Regular sessions, in person or online, with practical tools you apply in your daily life.",
    "process.s4t": "Progress & closure",
    "process.s4p":
      "We review your progress continuously until you reach your goals and feel balanced again.",

    "mod.1t": "In person in Mexicali",
    "mod.1p":
      "A private, comfortable, and discreet office in Mexicali, Baja California, designed so you feel at ease from the very first moment.",
    "mod.2t": "Online therapy",
    "mod.2p":
      "Video-call sessions with the same quality and confidentiality, wherever you are. Ideal if you live out of town or have a tight schedule.",

    "band.title": "The first step is the most important one",
    "band.sub": "Request your free 15-minute consultation. No cost, no commitment.",
    "band.cta1": "Book now",
    "band.cta2": "800 283 2791 ext. 33",

    "faq.eyebrow": "Frequently asked questions",
    "faq.title": "Let's clear up your doubts",
    "faq.q1": "How do I know if I need therapy?",
    "faq.a1":
      "If anxiety, sadness, or relationship conflicts are affecting your daily life, your sleep, or your work, therapy can help. You don't need to be \"really bad\" to seek support: therapy also helps you know yourself better and prevent bigger problems.",
    "faq.q2": "How long is each session and how often are they?",
    "faq.a2":
      "Sessions last about 50 minutes. Most people start with one session per week and adjust the frequency based on their progress and needs.",
    "faq.q3": "Does online therapy work as well as in-person?",
    "faq.a3":
      "Yes. Evidence shows online therapy is just as effective for most cases. You only need a private space, an internet connection, and the willingness to work on yourself.",
    "faq.q4": "Is everything we talk about confidential?",
    "faq.a4":
      "Absolutely. Confidentiality is the foundation of therapy and is protected by professional ethics. What you share in session stays between us, except for the exceptions established by law.",
    "faq.q5": "Do you see couples even if one partner has doubts?",
    "faq.a5":
      "Yes — it's very common for one partner to arrive with more doubts. In the first session we create a neutral space where both can express themselves; many couples discover the value of the process right there.",
    "faq.q6": "How do I book my first appointment?",
    "faq.a6":
      "You can call 800 283 2791 ext. 33, message me on WhatsApp, or fill out the contact form. I'll get back to you as soon as possible to schedule your free 15-minute consultation.",

    "contact.eyebrow": "Contact",
    "contact.title": "Book your free consultation",
    "contact.sub":
      "Write to me and I'll personally get back to you to schedule your first 15-minute consultation, free of charge.",
    "contact.phone": "Phone",
    "contact.loc": "Location",
    "contact.locv": "Mexicali, Baja California, ZIP 21376",
    "contact.hours": "Hours",
    "contact.hoursv": "Monday to Friday · by appointment",
    "contact.mode": "Format",
    "contact.modev": "In person and online",

    "form.name": "Full name *",
    "form.nameph": "Your name",
    "form.phone": "Phone / WhatsApp *",
    "form.email": "Email",
    "form.reason": "What kind of support are you looking for?",
    "form.opt1": "Individual therapy",
    "form.opt2": "Couples therapy",
    "form.opt3": "Anxiety / stress",
    "form.opt4": "Self-esteem",
    "form.opt5": "Other / not sure",
    "form.msg": "Tell me briefly about your situation",
    "form.msgph": "Write anything you'd like to share…",
    "form.pref": "Preferred time to contact you",
    "form.h1": "Morning (9:00 – 12:00)",
    "form.h2": "Afternoon (12:00 – 17:00)",
    "form.h3": "Evening (17:00 – 20:00)",
    "form.send": "Send message",
    "form.note": "Your information is confidential and will only be used to contact you.",

    "footer.tag": "Licensed Psychologist · National Registry of Professionals (SEP)",
    "footer.loc": "Mexicali, Baja California, Mexico",
    "footer.nav": "Navigation",
    "footer.contact": "Contact",
    "footer.pt": "Psychology Today profile",
    "footer.emergency":
      "If you are in crisis or thinking about harming yourself, call Línea de la Vida: 800 911 2000 (24 hours, free in Mexico). In the U.S., call or text 988.",
    "footer.rights": "All rights reserved.",
  };

  const ES = {}; // filled lazily from the DOM
  const ES_PH = {};
  let currentLang = "es";
  const langToggle = document.getElementById("langToggle");

  function cacheSpanish() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!(key in ES)) ES[key] = el.textContent;
    });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      const key = el.getAttribute("data-i18n-ph");
      if (!(key in ES_PH)) ES_PH[key] = el.getAttribute("placeholder") || "";
    });
  }

  function applyLang(lang) {
    const dict = lang === "en" ? EN : ES;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
      const key = el.getAttribute("data-i18n-ph");
      const val = lang === "en" ? EN[key] : ES_PH[key];
      if (val !== undefined) el.setAttribute("placeholder", val);
    });
    document.documentElement.lang = lang;
    langToggle.textContent = lang === "en" ? "ES" : "EN";
    currentLang = lang;
    try {
      localStorage.setItem("lang", lang);
    } catch (e) {
      /* storage unavailable — ignore */
    }
  }

  cacheSpanish();
  langToggle.addEventListener("click", () =>
    applyLang(currentLang === "es" ? "en" : "es")
  );

  try {
    if (localStorage.getItem("lang") === "en") applyLang("en");
  } catch (e) {
    /* ignore */
  }
})();
