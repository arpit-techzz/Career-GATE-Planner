// Generic POST helper
async function api(url, method = 'POST', body = {}) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: method === 'DELETE' ? null : JSON.stringify(body)
  });
  return res.json();
}

// Subject form
const subjectForm = document.getElementById('subjectForm');
if (subjectForm) {
  subjectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(subjectForm));
    await api('/api/subject', 'POST', data);
    location.reload();
  });

  document.querySelectorAll('.delete-subject').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this subject?')) return;
      await api(`/api/subject/${btn.dataset.id}`, 'DELETE');
      location.reload();
    });
  });

  document.querySelectorAll('.inc, .dec').forEach(btn => {
    btn.addEventListener('click', async () => {
      const val = Math.max(0, parseInt(btn.dataset.val));
      await api(`/api/subject/${btn.dataset.id}`, 'PUT', { completed_topics: val });
      location.reload();
    });
  });
}

// Task form
const taskForm = document.getElementById('taskForm');
if (taskForm) {
  taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(taskForm));
    await api('/api/task', 'POST', data);
    location.reload();
  });

  document.querySelectorAll('.delete-task').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this task?')) return;
      await api(`/api/task/${btn.dataset.id}`, 'DELETE');
      location.reload();
    });
  });

  document.querySelectorAll('.task-toggle').forEach(cb => {
    cb.addEventListener('change', async () => {
      const status = cb.checked ? 'Completed' : 'Pending';
      await api(`/api/task/${cb.dataset.id}`, 'PUT', { status });
      location.reload();
    });
  });
}

// Goal form
const goalForm = document.getElementById('goalForm');
if (goalForm) {
  goalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(goalForm));
    await api('/api/goal', 'POST', data);
    location.reload();
  });

  document.querySelectorAll('.delete-goal').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this goal?')) return;
      await api(`/api/goal/${btn.dataset.id}`, 'DELETE');
      location.reload();
    });
  });

  document.querySelectorAll('.goal-inc, .goal-dec').forEach(btn => {
    btn.addEventListener('click', async () => {
      let val = parseInt(btn.dataset.val);
      val = Math.max(0, Math.min(100, val));
      await api(`/api/goal/${btn.dataset.id}`, 'PUT', { progress: val });
      location.reload();
    });
  });
}