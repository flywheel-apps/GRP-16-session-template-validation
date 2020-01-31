# flywheel/grp16-session-template-validation

GRP-16 is a Flywheel analysis gear to validate sessions in project according to
session templates defined at the project level and report on the errors found.

## Inputs

This gear does not have any input.

## Configuration

### stop_after_n_sessions (int, optional) Default=-1

Number of sessions to process before stopping. If < 0, process all sessions. (Default=-1)

## Outputs

### validation-report.csv

This `csv` file contains the errors found for the session(s) that did
not pass the template validation.

For each such session, a row will populated with `session.id`, `session.label`, 
`subject.code` and errors for each `template` evaluated.

### template-list.yml 

This `yml` file contains the schema of the session templates defined for
the project at the time the gear was run.

## Troubleshooting
As with any gear, the Gear Logs are the first place to check when something appears 
to be amiss. If you are not a site admin, you will not be able to access the Jobs 
Log page, so do not delete your analysis until you have copied the gear log and 
downloaded the output files. Further, output files will not be available if you 
delete the analysis.

If you require further assistance from Flywheel, please include a copy of the gear 
log, the output validation-report and a link to the project on which you ran 
the gear in your correspondence for best results.
