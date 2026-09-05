/* Keeps the authenticated navigation identical on every product page. */
document.addEventListener('DOMContentLoaded', () => {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;

  const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';
  const workspace = [
    ['dashboard.html', 'speedometer2', 'Dashboard'],
    ['jobs.html', 'folder2-open', 'Jobs'],
    ['uploads.html', 'cloud-upload', 'Uploads'],
    ['mapping.html', 'columns-gap', 'Column mapping'],
    ['reconciliation.html', 'arrow-left-right', 'Reconcile'],
    ['results.html', 'table', 'Results']
  ];
  const administration = [
    ['manage_staff.html', 'people', 'Team'],
    ['subscription.html', 'credit-card', 'Subscription'],
    ['settings.html', 'gear', 'Settings']
  ];
  const navItem = ([href, icon, label]) => `<a href="${href}"${href === currentPage ? ' class="active" aria-current="page"' : ''}><i class="bi bi-${icon}" aria-hidden="true"></i>${label}</a>`;

  sidebar.innerHTML = `
    <a class="logo" href="dashboard.html" aria-label="Recon dashboard">Recon</a>
    <nav aria-label="Workspace">${workspace.map(navItem).join('')}</nav>
    <nav class="sidebar-admin" aria-label="Administration">${administration.map(navItem).join('')}</nav>
    <div class="sidebar-bottom"><button type="button" class="logout-btn" onclick="logout()"><i class="bi bi-box-arrow-right" aria-hidden="true"></i> Sign out</button></div>`;
});
