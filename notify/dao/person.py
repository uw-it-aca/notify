from uw_pws import PWS


def netid_from_eppn(eppn):
    return eppn.split("@")[0]


def get_person_by_netid(uwnetid):
    return PWS().get_person_by_netid(uwnetid)


def get_person_by_eppn(eppn):
    return get_person_by_netid(netid_from_eppn(eppn))
