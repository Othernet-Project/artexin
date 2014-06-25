% rebase('base.tpl', title='Pages')
<h1>Collected pages</h1>

<table>
    <thead>
    <tr>
    <th>ID</th>
    <th>Title</th>
    <th>Time</th>
    <th>Size</th>
    <th>Images</th>
    </tr>
    </thead>
    <tbody>
    % for p in pages:
        % include('_page_details.tpl', p=p)
    % end
    </tbody>
</ul>
