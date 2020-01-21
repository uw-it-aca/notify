from restclients_core.exceptions import InvalidNetID, DataFailureException
from notify.dao.person import get_person_by_eppn
import re


def validate_override_user(username):
    if not len(username):
        return ("No override user supplied, please enter a user to override"
                "as in the format of [netid]@washington.edu")

    match = re.search('@washington.edu', username)
    if match:
        try:
            person = get_person_by_eppn(username)
        except (InvalidNetID, DataFailureException) as ex:
            return ("Override user could not be found in the PWS. "
                    "Please enter a valid user to override as in the "
                    "format of [netid]@washington.edu You entered: ")
    else:
        return ("Override user must be formatted as [netid]@washington.edu. "
                "You entered: ")
