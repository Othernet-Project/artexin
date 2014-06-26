% rebase('base.tpl', title='Login')
<h1>Log in</h1>

<form action="/login/" method="POST">
    {{!h.vinput('redir', vals, _type='hidden')}}
    {{!h.form_errors(errors)}}
    <p>
    <label for="email">Email:</label>
    {{!h.vinput('email', vals, _type='text')}}
    {{!h.field_error(errors, 'email')}}
    </p>
    <p>
    <label for="password">Password:</label>
    {{!h.vinput('password', vals, _type='password')}}
    {{!h.field_error(errors, 'password')}}
    </p>
    <p>
    <label for="remember">Remember me:</label>
    {{!h.vselect('remember', (('s', 'for 30 minutes'), ('r', 'for 14 days')), vals)}}
    <span class="help">Use 30-minute session on public and multi-user computers</span>
    </p>
    <p class="buttons">
    <a class="button" href="/reset/">Reset your password</a>
    <button type="submit">Continue</button>
    </p>
</form>
    
