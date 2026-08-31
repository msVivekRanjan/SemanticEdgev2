/**
 * main.js
 * -------
 * SemanticEdge NVR Client-Side Controllers:
 * 1. Persistent Bottom Status Bar Poller (CPU, RAM, Engine, FPS, Health)
 * 2. Real-Time Camera Telemetry & Inference Stats Poller (500ms)
 * 3. Enhanced Object Detail Modal — Image preview, Description editor, Download, Delete
 * 4. Scroll Reveal Animations & Navigation Handlers
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── 1. Persistent Bottom Status Bar Poller ─────────────────────────────────
  const cpuStatEl    = document.getElementById('bar-stat-cpu');
  const memStatEl    = document.getElementById('bar-stat-mem');
  const gpuStatEl    = document.getElementById('bar-stat-gpu');
  const fpsStatEl    = document.getElementById('bar-stat-fps');
  const camsStatEl   = document.getElementById('bar-stat-cams');
  const healthStatEl = document.getElementById('bar-stat-health');

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
      } catch (_) { /* silent */ }
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

  // ── 3. Enhanced Object Detail Modal ──────────────────────────────────────
  const modalBackdrop = document.getElementById('nvr-detail-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  let _currentEventId = null;

  if (modalBackdrop) {

    /**
     * openDetailModal(eventId, className, timestamp, cameraName, confPct,
     *                 trackId, snapshotUrl, description, bbox, lineStatus)
     */
    window.openDetailModal = function(eventId, className, timestamp, cameraName, confPct,
                                      trackId, snapshotUrl, description, bbox, lineStatus) {

      _currentEventId = eventId;

      // Title
      const titleEl = document.getElementById('modal-title');
      if (titleEl) titleEl.textContent = `${(className || 'Object').charAt(0).toUpperCase() + (className || 'Object').slice(1)} Detection — Event #${eventId}`;

      // Class badge
      const badgeEl = document.getElementById('modal-class-badge');
      if (badgeEl) badgeEl.textContent = (className || 'OBJECT').toUpperCase();

      // Snapshot image
      const imgEl    = document.getElementById('modal-snapshot-img');
      const noImgEl  = document.getElementById('modal-no-img');
      if (snapshotUrl && snapshotUrl.trim() && snapshotUrl !== 'None') {
        imgEl.src = snapshotUrl;
        imgEl.style.display = 'block';
        noImgEl.style.display = 'none';
      } else {
        imgEl.style.display = 'none';
        noImgEl.style.display = 'flex';
      }

      // Metadata rows
      const timeEl   = document.getElementById('modal-time');
      const camEl    = document.getElementById('modal-camera');
      const confEl   = document.getElementById('modal-conf');
      const trackEl  = document.getElementById('modal-track');
      const bboxEl   = document.getElementById('modal-bbox');
      const lineEl   = document.getElementById('modal-line');

      if (timeEl)  timeEl.textContent  = timestamp   || 'N/A';
      if (camEl)   camEl.textContent   = cameraName  || '—';
      if (confEl)  confEl.textContent  = confPct     || '—';
      if (trackEl) trackEl.textContent = trackId > 0 ? `#${trackId}` : 'None';
      if (bboxEl)  bboxEl.textContent  = bbox        ? `[${bbox.join(', ')}]` : 'N/A';
      if (lineEl)  lineEl.textContent  = lineStatus  || 'none';

      // Description textarea
      const descInput = document.getElementById('modal-desc-input');
      if (descInput) descInput.value = description || '';

      // Download button href
      const downloadBtn = document.getElementById('modal-download-btn');
      if (downloadBtn) {
        if (snapshotUrl && snapshotUrl.trim() && snapshotUrl !== 'None') {
          downloadBtn.href = snapshotUrl;
          downloadBtn.style.opacity = '1';
          downloadBtn.style.pointerEvents = 'auto';
        } else {
          downloadBtn.href = '#';
          downloadBtn.style.opacity = '0.4';
          downloadBtn.style.pointerEvents = 'none';
        }
      }

      // Reset save button text
      const saveDescBtn = document.getElementById('modal-save-desc-btn');
      if (saveDescBtn) {
        saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px;">save</span><span>Update Description</span>';
        saveDescBtn.disabled = false;
      }

      modalBackdrop.classList.add('is-open');
    };

    // Close Handlers
    function closeModal() {
      modalBackdrop.classList.remove('is-open');
      _currentEventId = null;
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

    // ── Save Description via AJAX ──────────────────────────────────────
    const saveDescBtn = document.getElementById('modal-save-desc-btn');
    if (saveDescBtn) {
      saveDescBtn.addEventListener('click', async () => {
        if (!_currentEventId) return;

        const descInput = document.getElementById('modal-desc-input');
        const desc = descInput ? descInput.value.trim() : '';

        saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; animation: spin 1s linear infinite;">refresh</span><span>Saving...</span>';
        saveDescBtn.disabled = true;

        try {
          const csrfToken = document.cookie.split('; ')
            .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';

          const res = await fetch(`/nvr/api/detection/${_currentEventId}/update-description/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            },
            credentials: 'same-origin',
            body: JSON.stringify({ description: desc }),
          });

          if (res.ok) {
            saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; color: var(--success);">check_circle</span><span>Saved!</span>';
            setTimeout(() => {
              saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px;">save</span><span>Update Description</span>';
              saveDescBtn.disabled = false;
            }, 2000);
          } else {
            saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; color: var(--error);">error</span><span>Error — Retry</span>';
            saveDescBtn.disabled = false;
          }
        } catch (err) {
          saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; color: var(--error);">wifi_off</span><span>Network Error</span>';
          saveDescBtn.disabled = false;
        }
      });
    }

    // ── Delete Detection via AJAX ──────────────────────────────────────
    const deleteBtn = document.getElementById('modal-delete-btn');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        if (!_currentEventId) return;

        if (!confirm(`Are you sure you want to permanently delete Detection Event #${_currentEventId}? This action cannot be undone.`)) return;

        deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; animation: spin 1s linear infinite;">refresh</span><span>Deleting...</span>';
        deleteBtn.disabled = true;

        try {
          const csrfToken = document.cookie.split('; ')
            .find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';

          const res = await fetch(`/nvr/api/detection/${_currentEventId}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            credentials: 'same-origin',
          });

          if (res.ok) {
            closeModal();
            // Remove card from page without full reload
            const cards = document.querySelectorAll('.nvr-object-card');
            cards.forEach(card => {
              if (card.getAttribute('onclick') && card.getAttribute('onclick').includes(`openDetailModal(${_currentEventId},`)) {
                card.remove();
              }
            });
            // Also remove from review table rows
            const rows = document.querySelectorAll(`[data-event-id="${_currentEventId}"]`);
            rows.forEach(row => row.remove());
          } else {
            deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; color: var(--error);">error</span><span>Error</span>';
            deleteBtn.disabled = false;
          }
        } catch (err) {
          deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px; color: var(--error);">wifi_off</span><span>Network Error</span>';
          deleteBtn.disabled = false;
        }
      });
    }

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
