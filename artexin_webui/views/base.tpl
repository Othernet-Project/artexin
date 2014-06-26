<!doctype html>

<html>
    <head>
        <title>{{ get('title', 'Outernet Inc.') }} | ArtExIn</title>
        <link rel="stylesheet" href="/static/css/screen.css">
    </head>
    <body>
        <div id="nav">
        <h1><a href="/">ArtExIn Web UI</a></h1>
        <a class="green" href="/collections/">add pages</a>
        <a class="orange" href="/pages/">pages</a>
        <a href="/batches/">batches</a>
        % user=r.session.get('user')
        % if user:
        <a class="red" href="/logout/?redir={{h.quote(r.path)}}">log out</a>
        % else:
        <a class="green" href="/login/?redir={{h.quote(r.path)}}">log in</a>
        % end
        </div>
        <div id="content">
        {{!base}}
        </div>
        <div id="footer">
        <p class="copyright">&copy; 2014 Outernet Inc.</p>
        </div>
    </body>
</html>
