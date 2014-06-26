<tr>
<td><code><a href="/pages/{{ p.md5 }}">{{ h.trunc(p.md5, 8) }}</a></code></td>
<td><a href="{{ p.url }}">{{ h.trunc(p.title, 30) }}</a></td>
<td>{{ p.timestamp.strftime('%d %b %Y %H:%M UTC') }}</td>
<td>{{ h.hsize(p.size) }}</td>
<td>{{ p.images }}</td>
</tr>
