#!/usr/bin/env python
import os
import pandas as pd
import flywheel
import logging
from src.utils import get_analysis_parent, is_session_compliant

log = logging.getLogger(__name__)


def report_template_validation_on_project(project, debug=False):

    if debug:
        sessions = project.sessions()[:50]
    else:
        sessions = project.sessions()

    df = pd.DataFrame(columns=['session.id', 'subject.code', 'session.label'] + [f'template{i}' for i, _ in
                                                                                 enumerate(project.templates)])
    for i, session in enumerate(sessions):
        log.info(f'Processing session {session.id}...')
        is_valid, errors = is_session_compliant(session, project.templates)
        if not is_valid:
            log.info('Session %s failed. Logging failure', session.id)
            row = {'session.id': session.get('_id'),
                   'session.label': session.get('label'),
                   'subject.code': session.subject.code}
            row.update({f'template{i}': err for i, err in enumerate(errors)})
            df = df.append(row, ignore_index=True)

    if not df.empty:
        df.to_csv('/flywheel/v0/output/validation-report.csv', index=False)

    return 0


def main(gear_context):
    destination_id = gear_context.destination.get('id')
    origin = get_analysis_parent(gear_context.client, destination_id)
    return report_template_validation_on_project(origin, debug=gear_context.config.get('debug', False))


if __name__ == '__main__':
    with flywheel.GearContext() as gear_context:
        exit_status = main(gear_context)
    log.info('exit_status is %s', exit_status)
    os.sys.exit(exit_status)
