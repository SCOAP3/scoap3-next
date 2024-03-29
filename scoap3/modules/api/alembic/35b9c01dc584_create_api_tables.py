#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Create api tables."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '35b9c01dc584'
down_revision = '55dd6fe370e3'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('api_registrations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.Column('partner', sa.Boolean(name='partner'), server_default='0', nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('organization', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=False),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=1000), nullable=True),
    sa.Column('accepted', sa.Integer(), server_default='0', nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_api_registrations')),
    sa.UniqueConstraint('name', 'email', name='api_registrations_unique')
    )
    op.create_index(op.f('ix_api_registrations_email'), 'api_registrations', ['email'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    """Downgrade database."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_api_registrations_email'), table_name='api_registrations')
    op.drop_table('api_registrations')
    # ### end Alembic commands ###
