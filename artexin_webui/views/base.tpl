<!doctype html>

<html>
    <head>
        <title>{{ get('title', 'Outernet Inc.') }} | ArtExIn</title>
    </head>
    <body>
        <nav>
        % user=r.session.get('user')
        % if user:
        <a href="/logout/?redir={{h.quote(r.path)}}">log out</a>
        % else:
        <a href="/login/?redir={{h.quote(r.path)}}">log in</a>
        % end
        </nav>
        {{!base}}
    </body>
</html>
           
