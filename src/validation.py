#!/usr/bin/env python
import os
import copy
import logging
import argparse
from pathlib import Path
import pandas as pd
from ruamel import yaml
import flywheel
from src.utils import check_session_for_single_template


log = logging.getLogger(__name__)

CSV_BASENAME = 'validation-report.csv'
TEMPLATE_BASENAME = 'template-list.yml'


def is_session_compliant(session, templates):
    """Given a project-level templates and a session, check is session is compliant or not

    Args:
        session (flywheel.Session): A flywheel session object
        templates (list): A list of flywheel session template

    Returns:
        bool: True is compliant, False otherwise
        list: List of errors for each template
    """
    errors = []
    for template in templates:
        is_valid, error = check_session_for_single_template(session, copy.deepcopy(template))
        if is_valid:
            return True, None
        else:
            errors.append(error)
    return False, errors


def validate_session(session, templates, csv_output_path=None):
    """Validate session given template

    If errors are founds for session template, errors get logged to a csv file at path csv_output_path

    Args:
        session (flywheel.Session): A flywheel session object
        templates (list): A list of flywheel session template
        csv_output_path (Path-like): Path to output csv file storing errors

    Returns:
        int: 1 if errors was found during session validation, 0 otherwise
    """
    is_valid, errors = is_session_compliant(session, templates)
    if not is_valid:
        log.info('Session %s failed. Logging failure', session.id)
        row = {'session.id': session.get('_id'),
               'session.label': session.get('label'),
               'subject.code': session.subject.code}
        row.update({f'template{i}': err for i, err in enumerate(errors)})
        session_df = pd.DataFrame([row])

        if isinstance(session_df, pd.DataFrame):
            if csv_output_path and not os.path.isfile(csv_output_path) and (len(session_df) >= 1):
                session_df.to_csv(csv_output_path, index=False)
            elif csv_output_path and os.path.isfile(csv_output_path) and (len(session_df) >= 1):
                session_df.to_csv(csv_output_path, mode='a', header=False, index=False)
        return 1
    return 0


def report_validation_on_project(fw_client, project_id, stop_after_n_sessions=-1, output_dir=None):
    """Report on session failing project template validation

    Args:
        fw_client (flywheel.Client): A flywheel client
        project_id (str): A flywheel project ID
        stop_after_n_sessions (int): Number of sessions to process before stopping. If < 0, will process all sessions
         (default=-1)
        output_dir (Path-like): Path to directory where outputs are saved
    """

    project = fw_client.get(project_id)
    output_dir = Path(output_dir)
    csv_output_path = output_dir / CSV_BASENAME

    # save template at runtime
    if project.templates:
        with open(output_dir / TEMPLATE_BASENAME, 'w') as fid:
            yaml.dump({f'templates{i}': template for i, template in enumerate(project.templates)}, fid)
    else:
        log.info('Project does not have any templates defined. Nothing to report on.')
        return 0

    error_count = 0
    for i, session in enumerate(project.sessions.iter()):
        if 0 < stop_after_n_sessions <= i:
            break
        log.info(f'Processing session {session.id}...')
        error_count += validate_session(session, project.templates, csv_output_path=csv_output_path)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('project_path', help='Resolver path of the project to validate')
    parser.add_argument('--stop_after_n_sessions',
                        help='Number of sessions to process before stopping. If < 0, will process all sessions '
                             '(default=-1)',
                        type=int,
                        default=-1)
    parser.add_argument('--output_dir', help='Output directory (default=$PWD)', default=os.getcwd())
    parser.add_argument('--api_key', help='Use if not logged in via cli')

    args = parser.parse_args()
    if args.api_key:
        fw = flywheel.Client(args.api_key)
    else:
        fw = flywheel.Client()

    project = fw.lookup(args.project_path)
    if args.csv_output_path:
        csv_output_path = args.csv_output_path

    report_validation_on_project(
        fw_client=fw,
        project_id=project.id,
        stop_after_n_sessions=args.stop_after_n_sessions,
        output_dir=args.output_dir
    )
