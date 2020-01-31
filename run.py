#!/usr/bin/env python
import os
import flywheel
import logging
from pathlib import Path

from src.validation import report_validation_on_project
from src.utils import get_analysis_parent

log = logging.getLogger(__name__)

FW_ROOT = Path(os.environ.get('FLYWHEEL', '/flywheel/v0'))
OUTPUT_DIR = Path(FW_ROOT) / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args_from_context(gear_context):
    destination_id = gear_context.destination.get('id')
    origin = get_analysis_parent(gear_context.client, destination_id)
    # Return None if we failed to get the origin or destination project
    if not origin:
        return None

    template_validation_args = {
        'fw_client': gear_context.client,
        'project_id': origin.id,
        'stop_after_n_sessions': gear_context.config.get('stop_after_n_sessions', False),
        'output_dir': OUTPUT_DIR,
    }

    return template_validation_args


def main(gear_context):
    export_args = parse_args_from_context(gear_context)
    if not export_args:
        log.error('Exiting...')
        return 1
    else:
        error_count = report_validation_on_project(**export_args)

        # Update analysis label
        if error_count > 0:
            destination_id = gear_context.destination.get('id')
            analysis = gear_context.client.get(destination_id)
            analysis_label = f'grp16-session-template-validation_ERROR_SESSION_COUNT_{error_count}'
            log.info(f'Updating analysis={analysis.id} with label={analysis_label}')
            analysis.update({'label': analysis_label})

        if error_count == 0:
            log.info(f'Gear found {error_count} non compliant sessions')

        return 0


if __name__ == '__main__':
    with flywheel.GearContext() as gear_context:
        gear_context.init_logging()
        exit_status = main(gear_context)
    log.info('exit_status is %s', exit_status)
    os.sys.exit(exit_status)
