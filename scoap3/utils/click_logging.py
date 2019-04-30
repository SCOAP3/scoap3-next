import click


def info(msg):
    click.echo(msg)


def error(msg):
    click.echo(click.style(msg, fg='red'))


def rinfo(msg, record):
    """Helper for logging info about a record."""
    if record.json and 'control_number' in record.json:
        recid = record.json.get('control_number')
    else:
        recid = record.id

    info('%s: %s' % (recid, msg))


def rerror(msg, record):
    """Helper for logging errors about a record."""
    if record.json and 'control_number' in record.json:
        recid = record.json.get('control_number')
    else:
        recid = record.id

    error('%s: %s' % (recid, msg))
