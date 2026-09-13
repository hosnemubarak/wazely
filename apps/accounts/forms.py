from allauth.account.forms import (
    LoginForm as AllauthLoginForm,
    ResetPasswordForm as AllauthResetPasswordForm,
    ResetPasswordKeyForm as AllauthResetPasswordKeyForm,
    SignupForm as AllauthSignupForm,
)

# One summary line instead of Django's per-validator list (rendered by
# partials/_form_fields.html as the field's help text).
PASSWORD_HELP = "At least 8 characters, not a common or predictable pattern."


class LoginForm(AllauthLoginForm):
    """Login form tuned for the Wazely auth shell.

    allauth's under-field "Forgot your password?" help text is dropped: the
    single reset link renders on the password label row instead —
    ``partials/_form_fields.html`` checks ``show_forgot_password_link``.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["login"].widget.attrs["placeholder"] = "you@example.com"
        password = self.fields["password"]
        password.help_text = ""
        password.widget.attrs.pop("placeholder", None)
        password.show_forgot_password_link = True


class SignupForm(AllauthSignupForm):
    """Signup with a confirmed password: allauth builds ``password2`` from
    ``ACCOUNT_SIGNUP_FIELDS`` and enforces the match in ``clean()``."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        password1 = self.fields.get("password1")
        if password1 is not None:
            password1.help_text = PASSWORD_HELP
            password1.widget.attrs.pop("placeholder", None)
        password2 = self.fields.get("password2")
        if password2 is not None:
            password2.widget.attrs.pop("placeholder", None)


class ResetPasswordForm(AllauthResetPasswordForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"


class ResetPasswordKeyForm(AllauthResetPasswordKeyForm):
    """Set a new password without typing it twice.

    The reveal toggle and paste support make the confirmation field redundant
    (NIST SP 800-63B recommends against confirm-password as the primary typo
    guard). ``PasswordVerificationMixin.clean`` skips the equality check when
    ``password2`` is absent.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields.pop("password2", None)
        password1 = self.fields["password1"]
        password1.help_text = PASSWORD_HELP
        password1.widget.attrs.pop("placeholder", None)
