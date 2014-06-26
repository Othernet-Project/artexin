% rebase('base.tpl', title='Password reset')
<h1>Password reset</h1>

<form action="/reset/" method="POST">
    {{!h.form_errors(errors)}}
    % if r.session.get('user') is None:
    <p>
    <label for="email">Email:</label>
    {{!h.vinput('email', vals, _type='text')}}
    {{!h.field_error(errors, 'email')}}
    </p>
    % end
    <p>
    <label for="password">New password:</label>
    {{!h.vinput('password', vals, _type='password')}}
    {{!h.field_error(errors, 'password')}}
    </p>
    <p>
    <label for="confirm">Confirm password:</label>
    {{!h.vinput('confirm', vals, _type='password')}}
    {{!h.field_error(errors, 'confirm')}}
    </p>
    <p class="buttons">
    <button type="submit">Continue</button>
    </p>
</form>
