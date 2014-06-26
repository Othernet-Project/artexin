% rebase('base.tpl', title='Home')
% user = r.session.get('user')
<h1>Welcome {{ user.email }}</h1>
<ul class="home-menu">
    <li><a class="green" href="/collections/">Add new pages</a></li>
    <li><a class="orange" href="/pages/">Collected pages</a></li>
    <li><a href="/batches/">Completed batches</a></li>
    <li><a class="red" href="/logout/">Log out</a></li>
</ul>
