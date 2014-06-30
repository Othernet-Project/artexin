% rebase('base.tpl', title='Batch job %s' % batch.id)
<h1>Batch #{{ batch.id }}</h1>

<div class="batch-data">
    <div class="summary">
        % npages = len(batch.pages)
        <table>
        <tr>
        <th>initiated:</th>
        <td>{{ batch.started.strftime('%d %b %Y at %H:%M UTC') }}</td>
        </tr>
        <tr>
        <th>duration:</th>
        <td>{{ '%.2d' % batch.duration.seconds }}s</td>
        </tr>
        <tr>
        <th>pages:</th>
        <td>{{ npages }}</td>
        </tr>
        </table>
    </div>

    <div class="pages">
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
            % for p in batch.pages:
                % include('_page_details.tpl', p=p)
            % end 
            </tbody>
        </table>
    </div>
</div>
