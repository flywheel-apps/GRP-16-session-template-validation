"""Utility functions"""
import re
import copy
import logging

log = logging.getLogger(__name__)


def get_analysis_parent(fw_client, container_id):
    """Returns parent container id of the analysis container provided
    Args:
        fw_client (flywheel.Client): An instance of the Flywheel client
        container_id (str): A flywheel analysis container id

    Returns:
        (flywheel.Project): The container object or None if an exception is raised retrieving the container

    Raises:
        TypeError: If analysis parent is not of type 'project'
        Exception: If others exceptions occurred
    """
    try:
        container = fw_client.get(container_id)
        container_parent = fw_client.get(container.parent.id)
        if container_parent.container_type != 'project':
            raise TypeError('Analysis parent container must be of type project')
        log.info('Destination analysis %s  parent is a %s with id %s',
                 container.id, container_parent.container_type, container_parent.id)
        return container_parent
    except Exception as exc:
        log.error(exc, exc_info=True)
        return None


def check_req(cont, req_k, req_v):
    """Return (True, None) if container satisfies specific requirement or (False, error_msg) otherwise"""

    # If looking at classification, translate to list rather than dictionary
    if req_k == 'classification':
        cont_v = []
        for v in cont.get('classification', {}).values():
            cont_v.extend(v)
    else:
        cont_v = cont.get(req_k)

    if cont_v:
        if isinstance(req_v, dict):
            for k, v in req_v.items():
                is_satisfied, error = check_req(cont_v, k, v)
                if not is_satisfied:
                    return False, error
        elif isinstance(cont_v, list):
            found_in_list = False
            for v in cont_v:
                if re.search(req_v, v, re.IGNORECASE):
                    found_in_list = True
                    break
            if not found_in_list:
                return False, f'No {cont.container_type} {req_k} matching {req_v}'
        else:
            # Assume regex for now
            if not re.search(req_v, cont_v, re.IGNORECASE):
                return False, f'No {cont.container_type} {req_k} matching {req_v}'
    else:
        return False, f'No {cont.container_type} {req_k} matching {req_v} (None value found instead)'
    return True, None


def check_cont(cont, reqs):
    """Validate container against requirement

    Args:
        cont (flywheel.Container): A flywheel Container
        reqs (dict): A template requirement

    Returns:
        bool: True if valid, False otherwise
        str: Error found
    """
    for req_k, req_v in reqs.items():
        if req_k == 'files':
            for fr in req_v:
                fr_temp = fr.copy()  # so subsequent calls don't have their minimum missing
                min_count = fr_temp.pop('minimum')
                count = 0
                for f in cont.get('files', []):
                    is_satisfied, _ = check_cont(f, fr_temp)
                    if 'deleted' in f or not is_satisfied:
                        # Didn't find a match, on to the next one
                        continue

                    count += 1
                    if count >= min_count:
                        break

                if count < min_count:
                    return False, f'Failed to find {min_count} file(s) with requirement {fr_temp} ({count} found)'

        else:
            is_satisfied, error = check_req(cont, req_k, req_v)
            if not is_satisfied:
                return is_satisfied, error
    return True, None


def check_session_for_single_template(session, template):
    """Validate session against template

    Args:
        session (flywheel.Session): A flywheel session
        template (dict): A Flywheel session template

    Returns:
        bool: True if valid, False otherwise
        str: Error found
    """

    error = None
    s_requirements = template.get('session')
    a_requirements = template.get('acquisitions')

    if s_requirements:
        label = s_requirements.pop('label', None)
        if label:
            match = re.match(label, session.get('label', ''))
            if not match:
                return False, f'Session label "{session.get("label")}" does not match {label}'

            if not check_cont(session, s_requirements):
                return False, f'Session label "{session.get("label")}" does not match requirement {s_requirements}'

    if a_requirements:
        if not session.get('_id'):
            # New session, won't have any acquisitions. Compliance check fails
            return False, f'Session does not have an id'
        acquisitions = session.acquisitions()
        for req in a_requirements:
            req_temp = copy.deepcopy(req)
            min_count = req_temp.pop('minimum')
            count = 0
            for acq in acquisitions:
                is_valid, _ = check_cont(acq, req_temp)
                if not is_valid:
                    # Didn't find a match, on to the next one
                    continue
                count += 1
                if count >= min_count:
                    break
            if count < min_count:
                return False, f'Failed to find {min_count} acquisition(s) with requirement {req} ({count} found)'
    return True, error
