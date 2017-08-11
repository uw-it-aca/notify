import logging


class UserFilter(logging.Filter):
    """ Add user information to each log entry. """

    def filter(self, record):
        from userservice.user import UserService
        user_service = UserService()
        try:
            record.user = user_service.get_original_user() or "-"
            record.actas = (user_service.get_user() or "-").lower()
        except Exception as ex:
            record.user = "-"
            record.actas = "-"

        return True