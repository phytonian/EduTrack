// EduTrack Main JavaScript — Updated

document.addEventListener('DOMContentLoaded', function () {

  // ─── Auto-hide alerts after 5 seconds ─────────────────────────
  document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // ─── Confirm deletes ──────────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', function (e) {
      const msg = this.getAttribute('data-confirm') || 'Are you sure? This cannot be undone.';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ─── Bootstrap tooltips ───────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // ─── Progress bar animation ───────────────────────────────────
  document.querySelectorAll('.progress-bar[data-width]').forEach(bar => {
    const w = bar.getAttribute('data-width');
    bar.style.width = '0';
    setTimeout(() => {
      bar.style.transition = 'width 1s ease-in-out';
      bar.style.width = w + '%';
    }, 200);
  });

  // ─── Live table search ────────────────────────────────────────
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('keyup', function () {
      const val = this.value.toLowerCase();
      document.querySelectorAll('table tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(val) ? '' : 'none';
      });
    });
  }

  // ─── Image preview on file select ────────────────────────────
  document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
    input.addEventListener('change', function () {
      if (!this.files[0]) return;
      const reader = new FileReader();
      reader.onload = e => {
        let prev = document.getElementById('img-preview-' + (this.id || 'default'));
        if (!prev) {
          prev = document.createElement('img');
          prev.id = 'img-preview-' + (this.id || 'default');
          prev.className = 'img-thumbnail mt-2 rounded-circle';
          prev.style.cssText = 'width:80px;height:80px;object-fit:cover;';
          this.parentNode.appendChild(prev);
        }
        prev.src = e.target.result;
      };
      reader.readAsDataURL(this.files[0]);
    });
  });

  // ─── Character counter for textareas with maxlength ──────────
  document.querySelectorAll('textarea[maxlength]').forEach(ta => {
    const max = parseInt(ta.getAttribute('maxlength'));
    const counter = document.createElement('small');
    counter.className = 'text-muted d-block text-end';
    counter.textContent = `0 / ${max}`;
    ta.parentNode.appendChild(counter);
    ta.addEventListener('input', () => {
      const len = ta.value.length;
      counter.textContent = `${len} / ${max}`;
      counter.className = len > max * 0.9 ? 'text-warning d-block text-end' : 'text-muted d-block text-end';
    });
  });

  // ─── Smooth scroll ────────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // ─── Mark notification as read on click ──────────────────────
  document.querySelectorAll('[data-mark-read]').forEach(el => {
    el.addEventListener('click', function () {
      const id = this.getAttribute('data-mark-read');
      fetch(`/notification/${id}/read/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/json',
        }
      });
    });
  });

  // ─── CSRF cookie helper ───────────────────────────────────────
  function getCookie(name) {
    const val = `; ${document.cookie}`;
    const parts = val.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }

});
