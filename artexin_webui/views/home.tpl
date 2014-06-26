% rebase('base.tpl', title='Home')
% user = r.session.get('user')
<h1>Welcome {{ user.email }}</h1>
<ul class="home-menu">
    <li><a class="green" href="/collections/">Add new pages</a></li>
    <li><a class="orange" href="/pages/">Collected pages</a></li>
    <li><a href="/batches/">Completed batches</a></li>
    <li><a class="red" href="/logout/">Log out</a></li>
</ul>

<h2>Previous logins</h2>

<p>Your current IP is: {{ r.remote_addr }}</p>

<p>The table below show last 5 logins.</p>

<table>
    <thead>
        <tr>
        <th>IP address</th>
        <th>Time</th>
        </tr>
    </thead>
    <tbody>
    % if user.logins:
        % for login in reversed(user.logins[-5:]):
            <tr>
            <td>{{ login.ip_address }}</td>
            <td>{{ login.timestamp.strftime('%d %b at %H:%M UTC') }}</td>
            </tr>
        % end
    % else:
        <tr>
        <td colspan="2">No previous logins</td>
        </tr>
    % end
    </tbody>
</table>

