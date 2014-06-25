% rebase('base.tpl', title=page.title)
<h1>{{ page.title }}</h1>

<table>
    <tbody>
    <tr>
        <th>page title:</th>
        <td>{{ page.title }}</td>
    </tr>
    <tr>
        <th>original URL:</th>
        <td><a href="{{ page.url }}">{{ page.url }}</a></td>
    </tr>
    <tr>
        <th>payload:</th>
        <td>{{ h.hsize(page.size) }}</td>
    </tr>
    <tr>
        <th>number of images:</th>
        <td>{{ page.images }}</td>
    </tr>
    <tr>
        <th>retrieved at:</th>
        <td>{{ page.timestamp.strftime('%d %b %Y %H:%M UTC') }}</td>
    </tr>
    <tr>
        <th>batch:</th>
        <td><a href="/batches/{{ page.batch_id }}">{{page.batch_id}}</a></td>
    </tr>
    <tr>
        <th>file:</th>
        <td>{{ page.md5 }}.zip {{ h.yesno(exists, 'available', 'removed') }}</td>
    </tbody>
</table>
