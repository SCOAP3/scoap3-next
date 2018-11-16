import click


def info(msg):
    click.echo(msg)


def error(msg):
    click.echo(click.style(msg, fg='red'))


def rinfo(msg, record):
    """Helper for logging info about a record."""
    info('%s: %s' % (record.id, msg))


def rerror(msg, record):
    """Helper for logging errors about a record."""
    error('%s: %s' % (record.id, msg))
