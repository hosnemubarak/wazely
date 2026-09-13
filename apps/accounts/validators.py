from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RepeatedOrSequentialPasswordValidator:
    """Reject passwords Django's built-in validators let through.

    ``CommonPasswordValidator`` and ``NumericPasswordValidator`` miss passwords
    that are a single repeated character (``"aaaaaaaa"``) or a run of
    consecutive characters (``"abcdefgh"``, ``"87654321"``).
    """

    def validate(self, password: str, user: AbstractBaseUser | None = None) -> None:
        if len(set(password)) == 1:
            raise ValidationError(
                _("Your password can't be a single repeated character."),
                code="password_repeated",
            )
        if self._is_sequential(password):
            raise ValidationError(
                _("Your password can't be a simple sequence of characters."),
                code="password_sequential",
            )

    @staticmethod
    def _is_sequential(password: str) -> bool:
        if len(password) < 4:
            return False
        deltas = {ord(later) - ord(earlier) for earlier, later in zip(password, password[1:])}
        return deltas == {1} or deltas == {-1}

    def get_help_text(self) -> str:
        return str(
            _("Your password can't be a single repeated character or a simple sequence of characters.")
        )
