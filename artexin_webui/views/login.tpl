% rebase('base.tpl', title='Login')
<h1>Log in</h1>

<form action="/login/" method="POST">
    {{!h.tag('foo')}}
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
    {{!h.vselect('remember', (('s', 'disabled'), ('r', 'for 14 days')), vals)}}
    <span class="help">Leave this disabled on public and multi-user computers</span>
    </p>
    <p class="buttons">
    <button type="submit">Continue</button>
    </p>
</form>
    
