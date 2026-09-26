// Generic POST helper
async function api(url, method = 'POST', body = {}) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: method === 'DELETE' ? null : JSON.stringify(body)
  });
  const payload = await res.json();
  if (!res.ok || payload.status === 'error') {
    throw new Error(payload.message || 'Something went wrong');
  }
  return payload;
}

function handleError(error) {
  const message = document.createElement('div');
  message.className = 'toast error';
  message.textContent = error.message || 'Something went wrong';
  document.body.appendChild(message);
  setTimeout(() => message.remove(), 3500);
}

document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => form.querySelector('button[type="submit"]')?.setAttribute('disabled', 'true'));
});

document.querySelector('.menu-toggle')?.addEventListener('click', event => {
  const links = document.querySelector('.nav-links');
  const expanded = links.classList.toggle('open');
  event.currentTarget.setAttribute('aria-expanded', expanded);
});

const themeToggle = document.querySelector('.theme-toggle');
if (themeToggle) {
  if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
  });
}

// Subject form
const subjectForm = document.getElementById('subjectForm');
if (subjectForm) {
  subjectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(subjectForm));
    try { await api('/api/subject', 'POST', data); location.reload(); } catch (error) { handleError(error); }
  });

  document.querySelectorAll('.delete-subject').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this subject?')) return;
      try { await api(`/api/subject/${btn.dataset.id}`, 'DELETE'); location.reload(); } catch (error) { handleError(error); }
    });
  });

  document.querySelectorAll('.inc, .dec').forEach(btn => {
    btn.addEventListener('click', async () => {
      const val = Math.max(0, parseInt(btn.dataset.val));
      try { await api(`/api/subject/${btn.dataset.id}`, 'PUT', { completed_topics: val }); location.reload(); } catch (error) { handleError(error); }
    });
  });
}

// Task form
const taskForm = document.getElementById('taskForm');
if (taskForm) {
  taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(taskForm));
    try { await api('/api/task', 'POST', data); location.reload(); } catch (error) { handleError(error); }
  });

  document.querySelectorAll('.delete-task').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this task?')) return;
      try { await api(`/api/task/${btn.dataset.id}`, 'DELETE'); location.reload(); } catch (error) { handleError(error); }
    });
  });

  document.querySelectorAll('.task-toggle').forEach(cb => {
    cb.addEventListener('change', async () => {
      const status = cb.checked ? 'Completed' : 'Pending';
      try { await api(`/api/task/${cb.dataset.id}`, 'PUT', { status }); location.reload(); } catch (error) { handleError(error); }
    });
  });
}

// Goal form
const goalForm = document.getElementById('goalForm');
if (goalForm) {
  goalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(goalForm));
    try { await api('/api/goal', 'POST', data); location.reload(); } catch (error) { handleError(error); }
  });

  document.querySelectorAll('.delete-goal').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this goal?')) return;
      try { await api(`/api/goal/${btn.dataset.id}`, 'DELETE'); location.reload(); } catch (error) { handleError(error); }
    });
  });

  document.querySelectorAll('.goal-inc, .goal-dec').forEach(btn => {
    btn.addEventListener('click', async () => {
      let val = parseInt(btn.dataset.val);
      val = Math.max(0, Math.min(100, val));
      try { await api(`/api/goal/${btn.dataset.id}`, 'PUT', { progress: val }); location.reload(); } catch (error) { handleError(error); }
    });
  });
}

const taskSearch = document.getElementById('taskSearch');
const taskFilter = document.getElementById('taskFilter');
function filterTasks() {
  const search = (taskSearch?.value || '').toLowerCase();
  const filter = taskFilter?.value || 'all';
  document.querySelectorAll('tbody tr[data-status]').forEach(row => {
    row.hidden = (filter !== 'all' && row.dataset.status !== filter) ||
      (search && !row.dataset.search.includes(search));
  });
}
taskSearch?.addEventListener('input', filterTasks);
taskFilter?.addEventListener('change', filterTasks);