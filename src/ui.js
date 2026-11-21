import { PRESET_KEYS } from './config.js';

export function createUI(cameraCtrl, opts = {}) {
  const loaderEl = document.getElementById('loader-screen');
  const loaderBar = document.getElementById('loader-bar');
  const loaderText = document.getElementById('loader-text');
  const toggleBtn = document.getElementById('btn-toggle-ui');
  const presetBtns = Array.from(document.querySelectorAll('.preset-btn'));

  if (opts.ui === false) {
    document.body.classList.add('ui-none');
  }

  function setProgress(frac, label) {
    const pct = Math.max(4, Math.min(100, Math.round(frac * 100)));
    if (loaderBar) loaderBar.style.width = `${pct}%`;
    if (loaderText) {
      loaderText.textContent = label || `読み込み中… ${pct}%`;
    }
  }

  function hideLoader() {
    if (loaderEl) loaderEl.classList.add('hidden');
  }

  function setActivePreset(key) {
    for (const btn of presetBtns) {
      btn.classList.toggle('active', btn.dataset.cam === key);
    }
  }

  function toggleUI() {
    const hidden = document.body.classList.toggle('ui-hidden');
    if (toggleBtn) {
      const icon = toggleBtn.querySelector('.icon-eye');
      if (icon) icon.textContent = hidden ? '◎' : '◉';
    }
  }

  for (const btn of presetBtns) {
    btn.addEventListener('click', () => {
      const camKey = btn.dataset.cam;
      if (camKey) {
        cameraCtrl.setCam(camKey, false);
        setActivePreset(camKey);
      }
    });
  }

  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleUI);
  }

  cameraCtrl.setOnPresetChange(setActivePreset);

  window.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'h' || e.key === 'H') {
      toggleUI();
      return;
    }
    const idx = Number(e.key) - 1;
    if (idx >= 0 && idx < PRESET_KEYS.length) {
      cameraCtrl.setCam(PRESET_KEYS[idx], false);
    }
  });

  return {
    setProgress,
    hideLoader,
    setActivePreset,
    toggleUI,
  };
}
