% rebase('base.tpl', title='Collect webpages')
<h1>Resutls of collecting pages</h1>
<p>Took {{ time }} seconds</p>
<ul>
% for m in metadata:
    <li>
    <h2>{{ m['title'] }}</h2>
    <p><strong>{{ m['domain'] }}</strong> (<a href="{{ m['url'] }}">open page</a>)</p>
    <p><strong>number of images:</strong> {{ m['images'] }}</p>
    </li>
% end 
