/**
 * main.js
 * -------
 * SemanticEdge NVR Client-Side Controllers:
 * 1. Persistent Bottom Status Bar Poller (CPU, RAM, GPU/Engine, FPS, Health)
 * 2. Real-Time Camera Telemetry & Inference Stats Poller (500ms)
 * 3. Explore/Review Object Detail Modal Viewer
 * 4. Scroll Reveal Animations & Navigation Handlers
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Persistent Bottom Status Bar Poller ─────────────────────────────────
  const cpuStatEl     = document.getElementById('bar-stat-cpu');
  const memStatEl     = document.getElementById('bar-stat-mem');
  const gpuStatEl     = document.getElementById('bar-stat-gpu');
  const fpsStatEl     = document.getElementById('bar-stat-fps');
  const camsStatEl    = document.getElementById('bar-stat-cams');
  const healthStatEl  = document.getElementById('bar-stat-health');

  if (cpuStatEl) {
    async function updateSystemStatusBar() {
      try {
        const res = await fetch('/nvr/api/system-status/', { credentials: 'same-origin' });
        if (!res.ok) return;
        const data = await res.json();

        if (cpuStatEl) cpuStatEl.textContent = `${data.cpu_percent}%`;
        if (memStatEl) memStatEl.textContent = `${data.memory_percent}% (${data.memory_used_gb} GB)`;
        if (gpuStatEl) gpuStatEl.textContent = data.device || 'CPU';
        if (fpsStatEl) fpsStatEl.textContent = `${data.aggregate_fps} FPS`;
        if (camsStatEl) camsStatEl.textContent = `${data.active_cameras} / ${data.total_cameras}`;
        if (healthStatEl) healthStatEl.textContent = data.health || 'OPTIMAL';
      } catch (_) {
        // network silent ignore
      }
    }

    updateSystemStatusBar();
    setInterval(updateSystemStatusBar, 2500);
  }

  // ── 2. Real-Time Camera Telemetry Poller (Live Tab) ────────────────────────
  const statsPanel = document.getElementById('stats-panel');
  if (statsPanel) {
    const statsUrl = statsPanel.dataset.statsUrl;
    if (statsUrl) {
      const fpsEl        = document.getElementById('stat-fps');
      const totalEl      = document.getElementById('stat-total');
      const trackIdsEl   = document.getElementById('stat-track-ids');
      const countsListEl = document.getElementById('stat-counts');

      async function pollLiveCameraStats() {
        try {
          const res = await fetch(statsUrl, { credentials: 'same-origin' });
          if (!res.ok) return;
          const data = await res.json();

          if (fpsEl) fpsEl.textContent = (data.fps ?? 0).toFixed(1);
          if (totalEl) totalEl.textContent = data.total_objects ?? 0;
          if (trackIdsEl) trackIdsEl.textContent = (data.track_ids ?? []).join(', ') || '—';

          if (countsListEl && data.counts) {
            const keys = Object.keys(data.counts);
            if (keys.length === 0) {
              countsListEl.innerHTML = '<div style="font-size: 12px; color: var(--outline); font-family: var(--font-mono);">No objects detected</div>';
            } else {
              countsListEl.innerHTML = Object.entries(data.counts)
                .map(([cls, count]) =>
                  `<div class="stats-row">
                    <span class="stats-label" style="text-transform: capitalize;">${cls}</span>
                    <span class="stats-value">${count}</span>
                  </div>`
                ).join('');
            }
          }
        } catch (_) {}
      }

      pollLiveCameraStats();
      const pollInterval = setInterval(pollLiveCameraStats, 500);
      window.addEventListener('pagehide', () => clearInterval(pollInterval));
    }
  }

  // ── 3. Detail Modal Popup (Explore / Review) ──────────────────────────────
  const modalBackdrop = document.getElementById('nvr-detail-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  if (modalBackdrop) {
    window.openDetailModal = function(data) {
      const titleEl     = document.getElementById('modal-title');
      const timeEl      = document.getElementById('modal-time');
      const camEl       = document.getElementById('modal-camera');
      const confEl      = document.getElementById('modal-conf');
      const trackEl     = document.getElementById('modal-track');
      const bboxEl      = document.getElementById('modal-bbox');
      const lineEl      = document.getElementById('modal-line');

      if (titleEl) titleEl.textContent = `${data.class || 'Object'} Detection`;
      if (timeEl) timeEl.textContent = data.timestamp || 'N/A';
      if (camEl) camEl.textContent = data.camera_name || 'Primary Sensor';
      if (confEl) confEl.textContent = data.confidence_pct || '90%';
      if (trackEl) trackEl.textContent = data.track_id ? `#${data.track_id}` : 'None';
      if (bboxEl) bboxEl.textContent = data.bbox ? `[${data.bbox.join(', ')}]` : 'N/A';
      if (lineEl) lineEl.textContent = data.line_crossing_status || 'none';

      modalBackdrop.classList.add('is-open');
    };

    function closeModal() {
      modalBackdrop.classList.remove('is-open');
    }

    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', closeModal);
    }

    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }

  // ── 4. Scroll Reveal Animations (Public Pages) ────────────────────────────
  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length > 0) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    revealElements.forEach((el, index) => {
      observer.observe(el);
      if (index === 0) setTimeout(() => el.classList.add('is-visible'), 100);
    });
  }

});
