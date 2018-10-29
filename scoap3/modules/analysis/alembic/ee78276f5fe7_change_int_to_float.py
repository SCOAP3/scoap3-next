#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""change int to float"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee78276f5fe7'
down_revision = '485de8e5ab72'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column('analysis_gdp', 'value1', type_=sa.Float)
    op.alter_column('analysis_gdp', 'value2', type_=sa.Float)
    op.alter_column('analysis_gdp', 'value3', type_=sa.Float)
    op.alter_column('analysis_gdp', 'value4', type_=sa.Float)


def downgrade():
    """Downgrade database."""
    op.alter_column('analysis_gdp', 'value1', type_=sa.Integer)
    op.alter_column('analysis_gdp', 'value2', type_=sa.Integer)
    op.alter_column('analysis_gdp', 'value3', type_=sa.Integer)
    op.alter_column('analysis_gdp', 'value4', type_=sa.Integer)
