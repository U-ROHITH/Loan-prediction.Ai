/* ============================================================
   NEXUSBANK — Main Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Mobile Nav ── */
  const toggle   = document.querySelector('.nb-menu-toggle');
  const navLinks = document.querySelector('.nb-nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', () => navLinks.classList.toggle('open'));
  }

  /* ── Active nav link ── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nb-nav-links a').forEach(link => {
    if (link.getAttribute('href') === currentPath) link.classList.add('active');
  });

  /* ── Multi-step form ── */
  initMultiStepForm();

  /* ── Confidence bar animation (result page) ── */
  const bar = document.querySelector('.confidence-bar-fill');
  if (bar) {
    const target = parseFloat(bar.dataset.value) || 0;
    bar.style.width = '0%';
    requestAnimationFrame(() => setTimeout(() => { bar.style.width = target + '%'; }, 150));
  }

  /* ── Home loan chips ── */
  document.querySelectorAll('.loan-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.loan-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
    });
  });

});


/* ============================================================
   MULTI-STEP FORM
   ============================================================ */
function initMultiStepForm() {
  const steps    = document.querySelectorAll('.form-step');
  const siSteps  = document.querySelectorAll('.si-step');
  const siLines  = document.querySelectorAll('.si-line');
  const btnNexts = document.querySelectorAll('.btn-next');
  const btnBacks = document.querySelectorAll('.btn-back');
  const form     = document.getElementById('loan-form');

  if (!steps.length || !form) return;

  let current = 0;

  /* ── Navigate to step ── */
  function goTo(index) {
    steps[current].classList.remove('active');
    siSteps[current].classList.remove('active');

    if (index > current) {
      siSteps[current].classList.add('completed');
      siSteps[current].querySelector('.si-circle').innerHTML = checkSVG();
      if (siLines[current]) siLines[current].classList.add('completed');
    } else {
      siSteps[current].classList.remove('completed');
      siSteps[current].querySelector('.si-circle').innerHTML = current + 1;
      if (siLines[current]) siLines[current].classList.remove('completed');
    }

    current = index;
    steps[current].classList.add('active');
    siSteps[current].classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function checkSVG() {
    return `<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M3 8l3.5 3.5L13 4.5" stroke="white" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
  }

  /* ── Next buttons ── */
  btnNexts.forEach(btn => {
    btn.addEventListener('click', () => {
      if (validateStep(current) && current < steps.length - 1) goTo(current + 1);
    });
  });

  /* ── Back buttons ── */
  btnBacks.forEach(btn => {
    btn.addEventListener('click', () => {
      if (current > 0) goTo(current - 1);
    });
  });

  /* ── Submit: validate last step first ── */
  form.addEventListener('submit', (e) => {
    if (!validateStep(current)) {
      e.preventDefault();
      return;
    }
    const btn = document.getElementById('submit-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Analysing...'; }
  });

  /* ── Live EMI preview ── */
  const loanAmountInput = document.getElementById('loan_amount');
  const loanTermInput   = document.getElementById('loan_term');          // fixed: was 'loan_tenure'
  const purposeInputs   = document.querySelectorAll('input[name="loan_purpose"]');
  const emiPreview      = document.getElementById('emi_preview');
  const emiPreviewVal   = document.getElementById('emi_preview_val');
  const RATES = { Home: 8.75, Vehicle: 9.5, Education: 8.5, Personal: 12.0 };

  function updateEMIPreview() {
    if (!emiPreview || !emiPreviewVal) return;
    const amount = parseFloat(loanAmountInput?.value) || 0;
    const tenure = parseInt(loanTermInput?.value) || 0;
    let purpose  = 'Personal';
    purposeInputs.forEach(p => { if (p.checked) purpose = p.value; });
    const rate = RATES[purpose] || 12;

    if (amount > 0 && tenure > 0) {
      const r   = rate / 12 / 100;
      const emi = amount * r * Math.pow(1 + r, tenure) / (Math.pow(1 + r, tenure) - 1);
      emiPreviewVal.textContent = '₹' + Math.round(emi).toLocaleString('en-IN') + '/mo';
      emiPreview.style.display = 'block';
    } else {
      emiPreview.style.display = 'none';
    }
  }

  loanAmountInput?.addEventListener('input', updateEMIPreview);
  loanTermInput?.addEventListener('input', updateEMIPreview);
  purposeInputs.forEach(p => p.addEventListener('change', updateEMIPreview));

  /* ── Credit score hint ── */
  const creditInput = document.getElementById('credit_score');
  const creditHint  = document.getElementById('credit_hint');
  if (creditInput && creditHint) {
    creditInput.addEventListener('input', () => {
      const v = parseInt(creditInput.value);
      creditHint.className = 'input-hint';
      if (!v)      { creditHint.textContent = ''; return; }
      if (v >= 750){ creditHint.classList.add('good'); creditHint.textContent = 'Excellent — highest approval chance'; }
      else if (v >= 700){ creditHint.classList.add('good'); creditHint.textContent = 'Good — strong eligibility'; }
      else if (v >= 550){ creditHint.classList.add('warn'); creditHint.textContent = 'Fair — may affect approval'; }
      else { creditHint.classList.add('bad'); creditHint.textContent = 'Below minimum threshold (550)'; }
    });
  }
}


/* ============================================================
   STEP VALIDATION  (called by next buttons + submit)
   ============================================================ */
function validateStep(stepIndex) {
  const step     = document.querySelectorAll('.form-step')[stepIndex];
  const errAlert = step.querySelector('.error-alert');
  let valid = true;

  /* Validate text / number / select fields with [required] */
  step.querySelectorAll('input[required], select[required]').forEach(el => {
    // Skip radio buttons here — handled separately below
    if (el.type === 'radio') return;

    el.classList.remove('error');
    const val = el.value ? el.value.trim() : '';
    if (!val) {
      el.classList.add('error');
      valid = false;
    }
  });

  /* Validate radio group (loan purpose) */
  const purposeGrid = step.querySelector('.purpose-grid');
  if (purposeGrid) {
    const checked = purposeGrid.querySelector('input[type="radio"]:checked');
    if (!checked) {
      valid = false;
      purposeGrid.style.outline = '2px solid var(--danger)';
      purposeGrid.style.borderRadius = '8px';
      setTimeout(() => { purposeGrid.style.outline = ''; }, 2500);
    }
  }

  if (!valid && errAlert) {
    errAlert.classList.add('show');
    setTimeout(() => errAlert.classList.remove('show'), 3000);
  }

  return valid;
}
