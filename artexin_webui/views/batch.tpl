% rebase('base.tpl', title='Batch job %s' % batch.id)
<h1>Results of batch job {{ batch.id }}</h1>

<div class="summary">
    % npages = len(batch.pages)
    <p>Job was initiated on {{ batch.started.strftime('%d %b %Y at %H:%M UTC') }}</p>
    <p>Job took {{ '%.2d' % batch.duration.seconds }} {{ h.plur('second', batch.duration.seconds) }}.</p>
    <p>{{ npages }} {{ h.plur('page', npages) }} collected.</p>
</div>

<div class="pages">
    <ul>
    % for p in batch.pages:
        <li>
        <h2>{{ p.title }}</h2>
        <p><strong>original:</strong> <a href="{{ p.url }}">{{ p.url }}</a></p>
        <p><strong>file:</strong> {{ p.md5 }}.zip</p>
        <p><strong>size:</strong> {{ h.hsize(p.size) }}</p>
        <p><strong>images:</strong> {{ p.images }}</p>
        </li>
    % end 
    </ul>
</div>
