#!/usr/bin/env python
import os
from pathlib import Path
import pandas as pd
import flywheel
import logging
import copy
from src.utils import get_analysis_parent, is_session_compliant
from ruamel import yaml

log = logging.getLogger(__name__)

FW_ROOT = Path(os.environ.get('FLYWHEEL', '/flywheel/v0'))


def report_template_validation_on_project(project, analysis, stop_after_n_sessions=-1):

    df = pd.DataFrame(columns=['session.id', 'subject.code', 'session.label'] + [f'template{i}' for i, _ in
                                                                                 enumerate(project.templates)])
    output_dir = Path(FW_ROOT) / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    if project.templates:
        with open(output_dir/'template-list.yml', 'w') as fid:
            yaml.dump({f'templates{i}': template for i, template in enumerate(project.templates)}, fid)
    else:
        log.info('Project does not have any templates defined. Nothing to report on.')
        return 0

    for i, session in enumerate(project.sessions.iter()):

        if 0 < stop_after_n_sessions <= i:
            break

        log.info(f'Processing session {session.id}...')
        is_valid, errors = is_session_compliant(session, project.templates)
        if not is_valid:
            log.info('Session %s failed. Logging failure', session.id)
            row = {'session.id': session.get('_id'),
                   'session.label': session.get('label'),
                   'subject.code': session.subject.code}
            row.update({f'template{i}': err for i, err in enumerate(errors)})
            df = df.append(row, ignore_index=True)

    # saving df to output
    if not df.empty:
        df.to_csv(output_dir/'validation-report.csv', index=False)

        # Update analysis label
        analysis_label = f'grp16-session-template-validation_ERROR_SESSION_COUNT_{len(df)}'
        log.info(f'Updating analysis={analysis.id} with label={analysis_label}')
        analysis.update({'label': analysis_label})

    return 0


def main(gear_context):
    destination_id = gear_context.destination.get('id')
    destination = gear_context.client.get_analysis(destination_id)
    origin = get_analysis_parent(gear_context.client, destination_id)
    return report_template_validation_on_project(
        origin, destination, stop_after_n_sessions=gear_context.config.get('stop_after_n_sessions', False))


if __name__ == '__main__':
    with flywheel.GearContext() as gear_context:
        exit_status = main(gear_context)
    log.info('exit_status is %s', exit_status)
    os.sys.exit(exit_status)
