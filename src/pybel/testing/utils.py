# -*- coding: utf-8 -*-

"""Utilities for PyBEL testing."""

from uuid import uuid4

from requests.compat import urlparse

from ..constants import BEL_DEFAULT_NAMESPACE, FRAUNHOFER_RESOURCES
from ..manager.models import Namespace, NamespaceEntry
from ..struct.summary import get_annotation_values_by_annotation
from ..struct.summary.node_summary import get_names


def get_uri_name(url):
    """Get the file name from the end of the URL.

    Only useful for PyBEL's testing though since it looks specifically if the file is from the weird owncloud
    resources distributed by Fraunhofer.

    :type url: str
    :rtype: str
    """
    url_parsed = urlparse(url)

    if url.startswith(FRAUNHOFER_RESOURCES):
        return url_parsed.query.split('=')[-1]
    else:
        url_parts = url_parsed.path.split('/')
        return url_parts[-1]


def n():
    """Return a UUID string for testing.

    :rtype: str
    """
    return str(uuid4())[:15]


def make_dummy_namespaces(manager, graph, namespace_dict=None):
    """Make dummy namespaces for the test.

    :type manager: pybel.manager.Manager
    :type graph: pybel.BELGraph
    :type namespace_dict: dict[str,iter[str]]
    """
    node_names = get_names(graph)

    if namespace_dict:
        node_names.update(namespace_dict)

    for keyword, names in node_names.items():
        if keyword == BEL_DEFAULT_NAMESPACE:
            continue

        if keyword in graph.namespace_url and graph.namespace_url[keyword] in graph.uncached_namespaces:
            continue

        graph.namespace_url[keyword] = url = n()

        namespace = Namespace(keyword=keyword, url=url)
        manager.session.add(namespace)

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

    manager.session.commit()


def make_dummy_annotations(manager, graph):
    """Make dummy annotations for the test.

    :param pybel.manager.Manager manager:
    :param pybel.BELGraph graph:
    """
    annotation_names = get_annotation_values_by_annotation(graph)

    for keyword, names in annotation_names.items():
        graph.annotation_url[keyword] = url = n()

        namespace = Namespace(keyword=keyword, url=url, is_annotation=True)
        manager.session.add(namespace)

        for name in names:
            entry = NamespaceEntry(name=name, namespace=namespace)
            manager.session.add(entry)

    manager.session.commit()
