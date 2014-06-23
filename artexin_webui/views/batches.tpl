% rebase('base.tpl', title='Batches')
<h1>Previous batches</h1>

% if batches:
    <ul>
    % for batch in batches:
        <li><a href="/batches/{{ batch.id }}">{{ batch.id[:10] }}...</a> ({{ batch.finished.strftime('%Y-%m-%d %H:%M UTC') }})</li>
    % end
    </ul>
% else:
    <p>No batches</p>
% end
