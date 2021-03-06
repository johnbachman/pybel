# -*- coding: utf-8 -*-

"""Internal DSL functions for edges."""

from .utils import entity
from ..constants import (
    ACTIVITY, BEL_DEFAULT_NAMESPACE, DEGRADATION, EFFECT, FROM_LOC, LOCATION, MODIFIER, TO_LOC,
    TRANSLOCATION,
)

__all__ = [
    'activity',
    'degradation',
    'translocation',
    'extracellular',
    'intracellular',
    'secretion',
    'cell_surface_expression',
    'location',
]

intracellular = entity(name='intracellular', namespace='GOCC')
extracellular = entity(name='extracellular space', namespace='GOCC')
surface = entity(name='cell surface', namespace='GOCC')


def _activity_helper(modifier, location=None):
    """Make an activity dictionary.

    :param str modifier:
    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity`
    :rtype: dict
    """
    rv = {MODIFIER: modifier}

    if location:
        rv[LOCATION] = location

    return rv


def activity(name=None, namespace=None, identifier=None, location=None):
    """Make a subject/object modifier dictionary.

    :param str name: The name of the activity. If no namespace given, uses BEL default namespace
    :param Optional[str] namespace: The namespace of the activity
    :param Optional[str] identifier: The identifier of the name in the database
    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity` representing the location of the node
    :rtype: dict
    """
    rv = _activity_helper(ACTIVITY, location=location)

    if name or (namespace and identifier):
        rv[EFFECT] = entity(
            namespace=(namespace or BEL_DEFAULT_NAMESPACE),
            name=name,
            identifier=identifier
        )

    return rv


def degradation(location=None):
    """Make a degradation dictionary.

    :param Optional[dict] location: An entity from :func:`pybel.dsl.entity` representing the location of the node
    :rtype: dict
    """
    return _activity_helper(DEGRADATION, location=location)


def translocation(from_loc, to_loc):
    """Make a translocation dictionary.

    :param dict from_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :param dict to_loc: An entity dictionary from :func:`pybel.dsl.entity`
    :rtype: dict
    """
    rv = _activity_helper(TRANSLOCATION)
    rv[EFFECT] = {
        FROM_LOC: from_loc,
        TO_LOC: to_loc
    }
    return rv


def secretion():
    """Make a secretion translocation dictionary.

    This is a convenient wrapper representing the :func:`translocation` from the intracellular location to the
    extracellular space.

    :rtype: dict
    """
    return translocation(
        from_loc=intracellular,
        to_loc=extracellular
    )


def cell_surface_expression():
    """Make a cellular surface expression translocation dictionary.

    This is a convenient wrapper representing the :func:`translocation` from the intracellular location to the cell
    surface.

    :rtype: dict
    """
    return translocation(
        from_loc=intracellular,
        to_loc=surface,
    )


def location(identifier):
    """Make a location object modifier dictionary.

    :param entity identifier: A namespace/name/identifier pair

    Usage:

    X increases the abundance of Y in the cytoplasm

    .. code-block:: python

        from pybel import BELGraph
        from pybel.dsl import protein, location

        graph = BELGraph()

        source = protein('HGNC', 'IRAK1')
        target = protein('HGNC', 'IRF7, variants=[
            pmod('Ph', 'Ser', 477), pmod('Ph', 'Ser', 479),
        ])
        graph.add_increases(
            source,
            target,
            citation=...,
            evidence=...,
            object_modifier=location(entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
        )

    X increases the kinase activity of Y in the cytoplasm. In this case, the :func:`activity` function takes a location as
    an optional argument.

    .. code-block:: python

        from pybel import BELGraph
        from pybel.dsl import protein, location

        graph = BELGraph()

        source = ...
        target = ...
        graph.add_increases(
            source,
            target,
            citation=...,
            evidence=...,
            object_modifier=activity('kin', location=entity(namespace='GO', name='cytosol', identifier='GO:0005829')),
        )
    """
    return {
        LOCATION: identifier
    }
