/* ============================================================
   NEXUSBANK — Main Script
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Mobile Nav ── */
  const toggle = document.querySelector('.nb-menu-toggle');
  const navLinks = document.querySelector('.nb-nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }

  /* ── Highlight active nav link ── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nb-nav-links a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  /* ── Multi-step form ── */
  initMultiStepForm();

  /* ── Confidence bar animation (result page) ── */
  const bar = document.querySelector('.confidence-bar-fill');
  if (bar) {
    const target = parseFloat(bar.dataset.value) || 0;
    bar.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.width = target + '%'; }, 100);
    });
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
  const steps     = document.querySelectorAll('.form-step');
  const siSteps   = document.querySelectorAll('.si-step');
  const siLines   = document.querySelectorAll('.si-line');
  const btnNexts  = document.querySelectorAll('.btn-next');
  const btnBacks  = document.querySelectorAll('.btn-back');

  if (!steps.length) return;

  let current = 0;

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
      <path d="M3 8l3.5 3.5L13 4.5" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
  }

  btnNexts.forEach(btn => {
    btn.addEventListener('click', () => {
      if (validateStep(current)) {
        if (current < steps.length - 1) goTo(current + 1);
      }
    });
  });

  btnBacks.forEach(btn => {
    btn.addEventListener('click', () => {
      if (current > 0) goTo(current - 1);
    });
  });

  /* Live EMI preview */
  const loanAmountInput = document.getElementById('loan_amount');
  const loanTenureInput = document.getElementById('loan_tenure');
  const purposeInputs   = document.querySelectorAll('input[name="loan_purpose"]');
  const emiPreview      = document.getElementById('emi_preview');
  const emiPreviewVal   = document.getElementById('emi_preview_val');

  const RATES = { education: 8.5, home: 8.75, medical: 10.5, wedding: 11.0, personal: 12.0 };

  function updateEMIPreview() {
    if (!emiPreview) return;
    const amount  = parseFloat(loanAmountInput?.value) || 0;
    const tenure  = parseInt(loanTenureInput?.value) || 0;
    let purpose   = 'personal';
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
  loanTenureInput?.addEventListener('input', updateEMIPreview);
  purposeInputs.forEach(p => p.addEventListener('change', updateEMIPreview));

  /* Credit score hint */
  const creditInput = document.getElementById('credit_score');
  const creditHint  = document.getElementById('credit_hint');
  if (creditInput && creditHint) {
    creditInput.addEventListener('input', () => {
      const v = parseInt(creditInput.value);
      creditHint.className = 'input-hint';
      if (!v) { creditHint.textContent = ''; return; }
      if (v >= 750) { creditHint.classList.add('good'); creditHint.textContent = 'Excellent — highest approval chance'; }
      else if (v >= 700) { creditHint.classList.add('good'); creditHint.textContent = 'Good — strong eligibility'; }
      else if (v >= 650) { creditHint.classList.add('warn'); creditHint.textContent = 'Fair — may affect approval'; }
      else { creditHint.classList.add('bad'); creditHint.textContent = 'Below minimum threshold (650)'; }
    });
  }
}

/* ── Step Validation ── */
function validateStep(stepIndex) {
  const step     = document.querySelectorAll('.form-step')[stepIndex];
  const errAlert = step.querySelector('.error-alert');
  const required = step.querySelectorAll('[required]');
  let valid = true;

  required.forEach(el => {
    el.classList.remove('error');
    if (!el.value.trim()) {
      el.classList.add('error');
      valid = false;
    }
  });

  /* Check at least one radio selected in step 3 */
  const purposeGroup = step.querySelector('.purpose-grid');
  if (purposeGroup) {
    const checked = purposeGroup.querySelector('input[type="radio"]:checked');
    if (!checked) valid = false;
  }

  if (!valid && errAlert) {
    errAlert.classList.add('show');
    setTimeout(() => errAlert.classList.remove('show'), 3000);
  }
  return valid;
}
