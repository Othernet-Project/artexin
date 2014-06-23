% rebase('base.tpl', title='Pages')
<h1>Collected pages</h1>

<ul>
% for p in pages:
    <li>
    <h2><a href="/pages/{{ p.md5 }}">{{ p.title }}</a></h2>
    <p>{{ p.url }}</p>
    <p><strong>size:</strong> {{ p.size }} bytes</p>
    </li>
% end
</ul>
