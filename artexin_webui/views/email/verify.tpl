Use the following URL to access your account:

% scheme, host = r.urlparts[:2]
{{ scheme }}://{{ host }}/login/{{ token }}

The URL expires on {{ expiry.strftime('%a %d %b at %H:%M UTC') }}.

% include('email/signature', **locals())
