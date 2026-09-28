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

  // ── Restricted-Zone Intrusion Alert Audio & Visual Controller ──────────────
  let audioCtx = null;
  let audioUnlocked = false;

  function initAudio() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume().then(() => {
        audioUnlocked = true;
      }).catch(() => {});
    } else if (audioCtx && audioCtx.state === 'running') {
      audioUnlocked = true;
    }
  }

  // Auto-unlock audio context on first user interaction (handling browser autoplay policies)
  ['pointerdown', 'keydown', 'click'].forEach(evt => {
    document.addEventListener(evt, initAudio, { once: true, passive: true });
  });

  function playIntrusionChime() {
    try {
      if (!audioCtx) initAudio();
      if (!audioCtx || audioCtx.state !== 'running') return;

      const now = audioCtx.currentTime;

      // Two-tone professional security alert chime (D5: 587.33Hz -> A5: 880Hz)
      const osc1 = audioCtx.createOscillator();
      const osc2 = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      gainNode.connect(audioCtx.destination);
      gainNode.gain.setValueAtTime(0.001, now);
      gainNode.gain.exponentialRampToValueAtTime(0.18, now + 0.04);
      gainNode.gain.exponentialRampToValueAtTime(0.001, now + 0.48);

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, now);
      osc1.frequency.exponentialRampToValueAtTime(880, now + 0.12);

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(880, now + 0.12);

      osc1.connect(gainNode);
      osc2.connect(gainNode);

      osc1.start(now);
      osc1.stop(now + 0.48);
      osc2.start(now + 0.12);
      osc2.stop(now + 0.48);
    } catch (_) {
      // Audio autoplay restrictions or context error
    }
  }

  const toastContainer = document.getElementById('nvr-alert-toast-container');
  let lastSeenAlertId = null;
  const displayedAlertIds = new Set();

  function showIntrusionToast(alert) {
    if (!toastContainer) return;
    if (displayedAlertIds.has(alert.id)) return;
    displayedAlertIds.add(alert.id);

    const toast = document.createElement('div');
    toast.className = 'nvr-alert-toast';
    toast.dataset.alertId = alert.id;

    toast.innerHTML = `
      <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <div style="width: 26px; height: 26px; border-radius: 6px; background: rgba(255, 60, 60, 0.2); border: 1px solid rgba(255, 60, 60, 0.45); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <span class="material-symbols-outlined" style="font-size: 16px; color: #ff4d4d;">emergency</span>
          </div>
          <div>
            <div style="font-size: 12.5px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px;">
              <span>RESTRICTED-ZONE INTRUSION</span>
              <span style="font-size: 10px; font-family: var(--font-mono); color: var(--outline); font-weight: normal;">${alert.timestamp}</span>
            </div>
            <div style="font-size: 11.5px; color: #ff8888; font-weight: 600; margin-top: 1px;">
              ${alert.status}
            </div>
          </div>
        </div>
        <button type="button" class="btn btn--ghost btn--sm toast-dismiss-btn" style="padding: 2px; height: 22px; width: 22px; min-width: 0; color: var(--outline); border: none;" title="Dismiss notification">
          <span class="material-symbols-outlined" style="font-size: 16px;">close</span>
        </button>
      </div>

      <div style="font-size: 11.5px; color: var(--on-surface-variant); background: rgba(0,0,0,0.3); border-radius: 6px; padding: 6px 10px; font-family: var(--font-mono); border: 1px solid rgba(255,255,255,0.05);">
        <strong>${alert.class_name.toUpperCase()} #${alert.track_id}</strong> on <em>${alert.camera_name}</em> (${alert.confidence_pct})
      </div>

      <div style="display: flex; gap: 6px; margin-top: 2px;">
        <a href="${alert.review_url}" class="btn btn--secondary btn--sm" style="flex: 1; font-size: 11px; padding: 4px 6px; display: flex; align-items: center; justify-content: center; gap: 4px; text-decoration: none;">
          <span class="material-symbols-outlined" style="font-size: 14px;">manage_search</span>
          <span>Review Event</span>
        </a>
        <a href="${alert.explore_url}" class="btn btn--primary btn--sm" style="flex: 1; font-size: 11px; padding: 4px 6px; display: flex; align-items: center; justify-content: center; gap: 4px; text-decoration: none; background: rgba(109,94,245,0.85);">
          <span class="material-symbols-outlined" style="font-size: 14px;">forum</span>
          <span>Investigate</span>
        </a>
      </div>
    `;

    const dismissBtn = toast.querySelector('.toast-dismiss-btn');
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        dismissToast(toast);
      });
    }

    toastContainer.appendChild(toast);

    // Auto-dismiss after 12 seconds
    let timer = setTimeout(() => {
      dismissToast(toast);
    }, 12000);

    toast.addEventListener('mouseenter', () => clearTimeout(timer), { once: true });
  }

  function dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px) scale(0.95)';
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 250);
  }

  async function pollIntrusionAlerts() {
    try {
      const url = lastSeenAlertId === null 
        ? '/nvr/api/alerts/latest/' 
        : `/nvr/api/alerts/latest/?since_id=${lastSeenAlertId}`;
      const res = await fetch(url, { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();
      if (!data.success) return;

      if (lastSeenAlertId === null) {
        // Initial sync: bookmark to highest existing id so existing records don't trigger sound on page load
        lastSeenAlertId = data.max_id || 0;
        return;
      }

      if (data.alerts && data.alerts.length > 0) {
        playIntrusionChime();
        const sorted = [...data.alerts].sort((a, b) => a.id - b.id);
        sorted.forEach(alert => {
          showIntrusionToast(alert);
          if (alert.id > lastSeenAlertId) {
            lastSeenAlertId = alert.id;
          }
        });
      }

      if (data.max_id > lastSeenAlertId) {
        lastSeenAlertId = data.max_id;
      }
    } catch (_) { /* silent */ }
  }

  pollIntrusionAlerts();
  setInterval(pollIntrusionAlerts, 2500);

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

  // ── 3. Enhanced Object Detail Modal ────────────────────────────────────
  const modalBackdrop = document.getElementById('nvr-detail-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  let _currentEventId = null;

  function getCsrf() {
    return document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
  }

  if (modalBackdrop) {

    /**
     * openDetailModalFromEl(el)
     * Reads event data from element's dataset attributes.
     * Guaranteed fail-safe against string formatting or JSON parse errors.
     */
    window.openDetailModalFromEl = function(el) {
      if (!el) return;
      const target = el.closest('[data-event-id]') || el;
      const ds = target.dataset || {};
      let bbox = [];
      if (ds.bboxX1 !== undefined && ds.bboxX1 !== '') {
        bbox = [
          parseFloat(ds.bboxX1) || 0,
          parseFloat(ds.bboxY1) || 0,
          parseFloat(ds.bboxX2) || 0,
          parseFloat(ds.bboxY2) || 0,
        ];
      }

      // Backward-compatible fallback to data-event if present
      if (!ds.eventId && target.getAttribute('data-event')) {
        try {
          const d = JSON.parse(target.getAttribute('data-event'));
          _openModal(d);
          return;
        } catch (_) {}
      }

      _openModal({
        id: ds.eventId ? parseInt(ds.eventId, 10) : null,
        class: ds.class || 'object',
        timestamp: ds.timestamp || 'N/A',
        camera_name: ds.camera || '—',
        confidence_pct: ds.confidence || '—',
        track_id: ds.track || 'None',
        frame_number: ds.frame || '—',
        snapshot_url: ds.snapshot || '',
        description: ds.desc || '',
        bbox: bbox,
        line_crossing_status: ds.line || 'none',
      });
    };

    // Legacy positional-arg form kept for backward compat
    window.openDetailModal = function(eventId, className, timestamp, cameraName, confPct,
                                      trackId, snapshotUrl, description, bbox, lineStatus) {
      _openModal({ id: eventId, class: className, timestamp, camera_name: cameraName,
                   confidence_pct: confPct, track_id: trackId, snapshot_url: snapshotUrl,
                   description, bbox, line_crossing_status: lineStatus });
    };

    function _openModal(data) {
      _currentEventId = data.id || null;

      // Title
      const titleEl = document.getElementById('modal-title');
      const cls = (data.class || 'object');
      if (titleEl) titleEl.textContent = `${cls.charAt(0).toUpperCase() + cls.slice(1)} Detection Evidence — Event #${data.id || '?'}`;

      // Class badge
      const badgeEl = document.getElementById('modal-class-badge');
      if (badgeEl) badgeEl.textContent = cls.toUpperCase();

      // Snapshot image preview with loading and error handling
      const imgEl   = document.getElementById('modal-snapshot-img');
      const noImgEl = document.getElementById('modal-no-img');
      const snap    = (data.snapshot_url || '').trim();

      if (snap && snap !== 'None' && snap !== '') {
        imgEl.onload = () => {
          imgEl.style.display = 'block';
          if (noImgEl) noImgEl.style.display = 'none';
        };
        imgEl.onerror = () => {
          imgEl.style.display = 'none';
          if (noImgEl) noImgEl.style.display = 'flex';
        };
        imgEl.src = snap;
        imgEl.style.display = 'block';
        if (noImgEl) noImgEl.style.display = 'none';
      } else {
        imgEl.style.display = 'none';
        if (noImgEl) noImgEl.style.display = 'flex';
      }

      // Compute geometric dimensions from bounding box
      const bbox = Array.isArray(data.bbox) ? data.bbox : [];
      let dimsStr = '—';
      let centerStr = '—';
      if (bbox.length >= 4 && (bbox[0] !== 0 || bbox[2] !== 0)) {
        const w = Math.round(Math.abs(bbox[2] - bbox[0]));
        const h = Math.round(Math.abs(bbox[3] - bbox[1]));
        dimsStr = `${w} × ${h} px`;
        const cx = Math.round((bbox[0] + bbox[2]) / 2);
        const cy = Math.round((bbox[1] + bbox[3]) / 2);
        centerStr = `(${cx}, ${cy})`;
      }

      // Metadata setters
      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      set('modal-time',     data.timestamp      || 'N/A');
      set('modal-camera',   data.camera_name    || '—');
      set('modal-event-id', data.id ? `#${data.id}` : '—');
      set('modal-frame',    data.frame_number ? `Frame #${data.frame_number}` : '—');
      set('modal-conf',     data.confidence_pct || '—');
      const tid = parseInt(data.track_id);
      set('modal-track',    (!isNaN(tid) && tid > 0) ? `#${tid}` : 'Untracked / None');
      set('modal-bbox',     bbox.length >= 4 ? `[${bbox.map(v => Math.round(v)).join(', ')}]` : 'N/A');
      set('modal-dims',     dimsStr);
      set('modal-center',   centerStr);
      set('modal-line',     data.line_crossing_status || 'none');

      // Description textarea
      const descInput = document.getElementById('modal-desc-input');
      if (descInput) descInput.value = data.description || '';

      // Download button
      const downloadBtn = document.getElementById('modal-download-btn');
      if (downloadBtn) {
        if (snap && snap !== 'None' && snap !== '') {
          downloadBtn.href = snap;
          downloadBtn.download = `detection_${data.id || 'event'}.jpg`;
          downloadBtn.style.opacity = '1';
          downloadBtn.style.pointerEvents = 'auto';
        } else {
          downloadBtn.href = '#';
          downloadBtn.style.opacity = '0.35';
          downloadBtn.style.pointerEvents = 'none';
        }
      }

      // Reset Save Description button
      const saveBtn = document.getElementById('modal-save-desc-btn');
      if (saveBtn) {
        saveBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">save</span><span>Update Description</span>';
        saveBtn.disabled = false;
      }

      // Reset Delete button
      const delBtn = document.getElementById('modal-delete-btn');
      if (delBtn) {
        delBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">delete</span><span>Delete Event</span>';
        delBtn.disabled = false;
      }

      // Wire Inspect in Review button
      const reviewBtn = document.getElementById('modal-review-btn');
      if (reviewBtn) {
        let revUrl = '/nvr/review/';
        const params = [];
        if (data.class) params.push(`class=${encodeURIComponent(data.class.toLowerCase())}`);
        if (data.track_id && data.track_id !== '-1' && data.track_id !== 'None') params.push(`track_id=${encodeURIComponent(data.track_id)}`);
        if (data.id) params.push(`event_id=${encodeURIComponent(data.id)}`);
        if (params.length > 0) revUrl += '?' + params.join('&');
        reviewBtn.href = revUrl;
      }

      // Wire Investigate with Assistant button
      const investigateBtn = document.getElementById('modal-investigate-btn');
      if (investigateBtn) {
        investigateBtn.onclick = () => {
          closeModal();
          if (typeof window.openAssistantForEvent === 'function') {
            window.openAssistantForEvent(data.id, data);
          } else {
            window.location.href = `/nvr/explore/?event_id=${data.id || ''}&investigate=1`;
          }
        };
      }

      modalBackdrop.classList.add('is-open');
      modalBackdrop.setAttribute('aria-hidden', 'false');
    }

    // Close Handlers
    function closeModal() {
      modalBackdrop.classList.remove('is-open');
      modalBackdrop.setAttribute('aria-hidden', 'true');
      _currentEventId = null;
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);
    modalBackdrop.addEventListener('click', e => { if (e.target === modalBackdrop) closeModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

    // ── Save Description via AJAX ───────────────────────────────────────
    const saveDescBtn = document.getElementById('modal-save-desc-btn');
    if (saveDescBtn) {
      saveDescBtn.addEventListener('click', async () => {
        if (!_currentEventId) return;
        const descInput = document.getElementById('modal-desc-input');
        const desc = descInput ? descInput.value.trim() : '';

        saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">refresh</span><span>Saving...</span>';
        saveDescBtn.disabled = true;

        try {
          const csrfToken = getCsrf();
          const res = await fetch(`/nvr/api/detection/${_currentEventId}/update-description/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            credentials: 'same-origin',
            body: JSON.stringify({ description: desc }),
          });
          if (res.ok) {
            // Update the dataset on the card so next click reflects the new description
            const card = document.querySelector(`[data-event-id="${_currentEventId}"]`);
            if (card) {
              card.dataset.desc = desc;
              if (card.getAttribute('data-event')) {
                try {
                  const d = JSON.parse(card.getAttribute('data-event') || '{}');
                  d.description = desc;
                  card.setAttribute('data-event', JSON.stringify(d));
                } catch(_) {}
              }
            }
            saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:var(--success);">check_circle</span><span>Saved!</span>';
            setTimeout(() => {
              saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">save</span><span>Update Description</span>';
              saveDescBtn.disabled = false;
            }, 2500);
          } else {
            saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:var(--error);">error</span><span>Error — Retry</span>';
            saveDescBtn.disabled = false;
          }
        } catch (_) {
          saveDescBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:var(--error);">wifi_off</span><span>Network Error</span>';
          saveDescBtn.disabled = false;
        }
      });
    }

    // ── Delete Detection via AJAX ────────────────────────────────────────
    const deleteBtn = document.getElementById('modal-delete-btn');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async () => {
        if (!_currentEventId) return;
        if (!confirm(`Permanently delete Detection Event #${_currentEventId}? This cannot be undone.`)) return;

        deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;">refresh</span><span>Deleting...</span>';
        deleteBtn.disabled = true;

        try {
          const csrfToken = getCsrf();
          const res = await fetch(`/nvr/api/detection/${_currentEventId}/delete/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            credentials: 'same-origin',
          });
          if (res.ok) {
            closeModal();
            // Remove card from DOM using data-event-id attribute
            document.querySelectorAll(`[data-event-id="${_currentEventId}"]`).forEach(el => {
              el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
              el.style.opacity = '0';
              el.style.transform = 'scale(0.9)';
              setTimeout(() => el.remove(), 300);
            });
          } else {
            deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:var(--error);">error</span><span>Error</span>';
            deleteBtn.disabled = false;
          }
        } catch (_) {
          deleteBtn.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;color:var(--error);">wifi_off</span><span>Network Error</span>';
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
