# /animeu/admin/queries.py
#
# Query functions used to populate the admin page.
#
# See /LICENCE.md for Copyright information
"""Query functions used to populate the admin page."""
from sqlalchemy.sql import select, or_
from animeu.app import db

DATATABLES_NO_LIMIT = -1

def maybe_get(indexable, *keys, default=None):
    """Maybe get a nested value via a series of indexes."""
    current = indexable
    for key in keys:
        try:
            current = current[key]
        except (KeyError, IndexError):
            return default
    return current

def apply_pagination_parameters_to_datatables_query(query, parameters):
    """Apply the pagination parameters to a datatables query."""
    offset = maybe_get(parameters, "start", default=0)
    query = query.offset(offset)
    limit = maybe_get(parameters, "length", default=DATATABLES_NO_LIMIT)
    if limit != DATATABLES_NO_LIMIT:
        query = query.limit(limit)
    return query

# pylint: disable=invalid-name
def apply_filtering_parameters_to_datatables_query(Model,
                                                   query,
                                                   allowed_columns,
                                                   parameters):
    """Apply the filtering parameters to a datatables query."""
    column_parameters = maybe_get(parameters, "columns", default=[])
    maybe_search_text = maybe_get(parameters, "search", "value")
    inclusion_conditions = []
    if maybe_search_text:
        for column in allowed_columns:
            if not isinstance(column.type, db.String):
                continue
            inclusion_conditions.append(column.contains(maybe_search_text))
    for column_parameter in column_parameters:
        maybe_column_name = maybe_get(column_parameter, "name")
        if maybe_column_name is None or \
                maybe_column_name not in Model.__table__.columns:
            continue
        maybe_search_text = maybe_get(column_parameter, "search", "value")
        if not maybe_search_text:
            continue
        column = Model.__table__.columns[maybe_column_name]
        if column not in allowed_columns:
            continue
        inclusion_conditions.append(column.contains(maybe_search_text))
    return query.where(or_(*inclusion_conditions))

# pylint: disable=invalid-name
def apply_ordering_parameters_to_datatables_query(Model,
                                                  query,
                                                  allowed_columns,
                                                  parameters):
    """Apply ordering parameters to a datatables query."""
    for order_parameter in maybe_get(parameters, "order", default=[]):
        maybe_column_index = maybe_get(order_parameter, "column")
        if maybe_column_index is None:
            continue
        maybe_column_name = \
            maybe_get(parameters, "columns", maybe_column_index, "name")
        if maybe_column_name is None or \
                maybe_column_name not in Model.__table__.columns:
            continue
        column = Model.__table__.columns[maybe_column_name]
        if column not in allowed_columns:
            continue
        order_direction = maybe_get(order_parameter, "dir")
        if order_direction == "asc":
            query = query.order_by(column)
        elif order_direction == "desc":
            query = query.order_by(column.desc())
    return query

# pylint: disable=invalid-name
def get_base_datatables_query(Model, parameters, ignore_columns=None):
    """Query the users table using the datatables style parameters."""
    column_parameters = maybe_get(parameters, "columns", default=[])
    select_columns = []
    for column_parameter in column_parameters:
        maybe_column_name = maybe_get(column_parameter, "name")
        if maybe_column_name is None or \
                (ignore_columns is not None and maybe_column_name in ignore_columns) \
                or maybe_column_name not in Model.__table__.columns:
            continue
        column = Model.__table__.columns[maybe_column_name]
        select_columns.append(column)
    query = select(select_columns)
    query = apply_filtering_parameters_to_datatables_query(Model,
                                                           query,
                                                           select_columns,
                                                           parameters)
    query = apply_ordering_parameters_to_datatables_query(Model,
                                                          query,
                                                          select_columns,
                                                          parameters)
    return query
