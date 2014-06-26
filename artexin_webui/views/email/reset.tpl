Use the following URL to reset your password:

% scheme, host = r.urlparts[:2]
{{ scheme }}://{{ host }}/reset/{{ token }}

The URL expires on {{ expiry.strftime('%a %d %b at %H:%M UTC') }}.

% include('email/signature', **locals())
