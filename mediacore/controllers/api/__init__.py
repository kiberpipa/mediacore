# This file is a part of MediaCore, Copyright 2009 Simple Station Inc.
#
# MediaCore is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MediaCore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from sqlalchemy import sql

class APIException(Exception):
    """
    API Usage Error -- wrapper for providing helpful error messages.
    TODO: Actually display these messages!!
    """

def get_order_by(order, columns):
    """ Discover the order by passed in """

    # Split the order into two parts, column and direction
    if not order:
        order_col, order_dir = 'publish_on', 'desc'
    else:
        try:
            order_col, order_dir = unicode(order).strip().lower().split(' ')
            assert order_dir in ('asc', 'desc')
        except:
            raise APIException, 'Invalid order format, must be "column asc/desc", given "%s"' % order

    # Get the order clause for the given column name
    try:
        order_attr = columns[order_col]
    except KeyError:
        raise APIException, 'Not allowed to order by "%s", please pick one of %s' % (order_col, ', '.join(columns.keys()))

    # Normalize to something that can be used in a query
    if isinstance(order_attr, basestring):
        order = sql.text(order_attr % (order_dir == 'asc' and 'asc' or 'desc'))
    else:
        # Assume this is an sqlalchemy InstrumentedAttribute
        order = getattr(order_attr, order_dir)()

    return order
