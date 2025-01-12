import requests
import json

from server import app
from server.models import FlagStatus, SubmitResult


RESPONSES = {
    FlagStatus.QUEUED: ['timeout', 'game not started', 'try again later', 'game over', 'is not up',
                        'no such flag'],
    FlagStatus.ACCEPTED: ['accepted', 'congrat', 'accept'],
    FlagStatus.REJECTED: ['bad', 'wrong', 'expired', 'unknown', 'your own',
                          'too old', 'not in database', 'already submitted', 'invalid flag', 'duplicated'],
}
# The RuCTF checksystem adds a signature to all correct flags. It returns
# "invalid flag" verdict if the signature is invalid and "no such flag" verdict if
# the signature is correct but the flag was not found in the checksystem database.
#
# The latter situation happens if a checker puts the flag to the service before putting it
# to the checksystem database. We should resent the flag later in this case.


TIMEOUT = 5


def submit_flags(flags, config):
    r = requests.post(config['SYSTEM_URL'],
                    json={
                        'flags': [item.flag for item in flags],
                        'token': config['SYSTEM_TOKEN'],
                    }, timeout=TIMEOUT)

    unknown_responses = set()

    counter = -1
    for item in json.loads(r.text):
        response = item.strip()

        response_lower = response.lower()
        for status, substrings in RESPONSES.items():
            if any(s in response_lower for s in substrings):
                found_status = status
                break
        else:
            found_status = FlagStatus.QUEUED
            if response not in unknown_responses:
                unknown_responses.add(response)
                app.logger.warning('Unknown checksystem response (flag will be resent): %s', response)
        counter += 1
        yield SubmitResult(flags[counter].flag, found_status, response)
