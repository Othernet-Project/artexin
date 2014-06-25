% rebase('base.tpl', title='Batches')
<h1>Completed batches</h1>

<table>
    <thead>
    <tr>
    <th>ID</th>
    <th>Time</th>
    </tr>
    </thead>
    <tbody>
    % if batches:
        % for batch in batches:
            <tr>
            <td><code><a href="/batches/{{ batch.id }}">{{ batch.id }}</a></code></td>
            <td>{{ batch.finished.strftime('%Y-%m-%d %H:%M UTC') }}</td>
            </tr>
        % end
    % else:
        <tr>
        <td colspan="2">No batches</td>
        </tr>
    % end
    </tbody>
</table>
