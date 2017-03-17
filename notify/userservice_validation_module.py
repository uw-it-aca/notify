from uw_pws import PWS
from restclients_core.exceptions import InvalidNetID, DataFailureException
from notify.utilities import netid_from_eppn
import re


def validate_override_user(username):
    if not len(username):
        return ("No override user supplied, please enter a user to override"
                "as in the format of [netid]@washington.edu")

    match = re.search('@washington.edu', username)
    if match:
        try:
            netid = netid_from_eppn(username)
            pws_person = PWS().get_person_by_netid(netid)
        except (InvalidNetID, DataFailureException) as ex:
            return ("Override user could not be found in the PWS. "
                    "Please enter a valid user to override as in the "
                    "format of [netid]@washington.edu You entered: ")
    else:
        return ("Override user must be formatted as [netid]@washington.edu. "
                "You entered: ")
