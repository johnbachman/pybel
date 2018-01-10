# -*- coding: utf-8 -*-

import logging
import os
import tempfile
import time
import unittest
from pathlib import Path

import networkx as nx
from six import BytesIO, StringIO

from pybel import (
    BELGraph, from_bytes, from_cx, from_cx_jsons, from_json, from_json_file, from_jsons, from_lines, from_ndex,
    from_path, from_pickle, from_url, to_bel_lines, to_bytes, to_csv, to_cx, to_cx_jsons, to_graphml, to_gsea, to_json,
    to_json_file, to_jsons, to_ndex, to_pickle, to_sif,
)
from pybel.constants import *
from pybel.dsl import gene
from pybel.examples import sialic_acid_graph
from pybel.io.io_exceptions import ImportVersionWarning, import_version_message_fmt
from pybel.io.ndex_utils import NDEX_PASSWORD, NDEX_USERNAME
from pybel.parser import BelParser
from pybel.parser.parse_exceptions import *
from pybel.struct.summary import get_syntax_errors
from pybel.utils import hash_node
from tests.constants import (
    AKT1, BelReconstitutionMixin, CASP8, EGFR, FADD, TemporaryCacheClsMixin, TestTokenParserBase, citation_1,
    evidence_1, test_bel_isolated, test_bel_misordered, test_bel_simple, test_bel_slushy, test_bel_thorough,
    test_citation_dict, test_evidence_text, test_set_evidence,
)
from tests.mocks import mock_bel_resources

logging.getLogger('requests').setLevel(logging.WARNING)
log = logging.getLogger(__name__)

testan1 = '1'


def do_remapping(original, reconstituted):
    """Remaps nodes to use the reconstitution tests
    
    :param BELGraph original: The original bel graph 
    :param BELGraph reconstituted: The reconstituted BEL graph from CX input/output
    """
    node_mapping = dict(enumerate(sorted(original.nodes_iter(), key=hash_node)))
    try:
        nx.relabel.relabel_nodes(reconstituted, node_mapping, copy=False)
    except KeyError as e:
        missing_nodes = set(node_mapping) - set(reconstituted.nodes_iter())
        log.exception('missing %s', [node_mapping[n] for n in missing_nodes])
        raise e


class TestExampleInterchange(unittest.TestCase):
    def help_test_equal(self, graph):
        """Checks that a graph is equal to the sialic acid graph example

        :type graph: pybel.BELGraph
        """
        self.assertEqual(set(sialic_acid_graph.nodes_iter()),
                         set(graph.nodes_iter()))

        self.assertEqual(set(sialic_acid_graph.edges_iter()),
                         set(graph.edges_iter()))

    def test_example_bytes(self):
        graph_bytes = to_bytes(sialic_acid_graph)
        graph = from_bytes(graph_bytes)
        self.help_test_equal(graph)

    def test_example_pickle(self):
        bio = BytesIO()
        to_pickle(sialic_acid_graph, bio)
        bio.seek(0)
        graph = from_pickle(bio)
        self.help_test_equal(graph)

    def test_thorough_json(self):
        graph_json_dict = to_json(sialic_acid_graph)
        graph = from_json(graph_json_dict)
        self.help_test_equal(graph)

    def test_thorough_jsons(self):
        graph_json_str = to_jsons(sialic_acid_graph)
        graph = from_jsons(graph_json_str)
        self.help_test_equal(graph)

    def test_thorough_json_file(self):
        sio = StringIO()
        to_json_file(sialic_acid_graph, sio)
        sio.seek(0)
        graph = from_json_file(sio)
        self.help_test_equal(graph)


class TestInterchange(TemporaryCacheClsMixin, BelReconstitutionMixin):
    @classmethod
    def setUpClass(cls):
        super(TestInterchange, cls).setUpClass()

        @mock_bel_resources
        def get_thorough_graph(mock):
            return from_path(test_bel_thorough, manager=cls.manager, allow_nested=True)

        cls.thorough_graph = get_thorough_graph()

        @mock_bel_resources
        def get_slushy_graph(mock):
            return from_path(test_bel_slushy, manager=cls.manager)

        cls.slushy_graph = get_slushy_graph()

        @mock_bel_resources
        def get_simple_graph(mock_get):
            return from_url(Path(test_bel_simple).as_uri(), manager=cls.manager)

        cls.simple_graph = get_simple_graph()

        @mock_bel_resources
        def get_isolated_graph(mock_get):
            return from_path(test_bel_isolated, manager=cls.manager)

        cls.isolated_graph = get_isolated_graph()

        @mock_bel_resources
        def get_misordered_graph(mock_get):
            return from_path(test_bel_misordered, manager=cls.manager, citation_clearing=False)

        cls.misordered_graph = get_misordered_graph()

    def test_thorough_path(self):
        self.bel_thorough_reconstituted(self.thorough_graph)

    def test_thorough_bytes(self):
        graph_bytes = to_bytes(self.thorough_graph)
        graph = from_bytes(graph_bytes)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_pickle(self):
        bio = BytesIO()
        to_pickle(self.thorough_graph, bio)
        bio.seek(0)
        graph = from_pickle(bio)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_json(self):
        graph_json_dict = to_json(self.thorough_graph)
        graph = from_json(graph_json_dict)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_jsons(self):
        graph_json_str = to_jsons(self.thorough_graph)
        graph = from_jsons(graph_json_str)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_json_file(self):
        sio = StringIO()
        to_json_file(self.thorough_graph, sio)
        sio.seek(0)
        graph = from_json_file(sio)
        self.bel_thorough_reconstituted(graph)

    def test_thorough_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_csv(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_csv(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_sif(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_sif(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_gsea(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'w') as f:
            to_gsea(self.thorough_graph, f)

        os.close(handle)
        os.remove(path)

    def test_thorough_cx(self):
        graph_cx_json_dict = to_cx(self.thorough_graph)
        reconstituted = from_cx(graph_cx_json_dict)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False)

    def test_thorough_cxs(self):
        graph_cx_str = to_cx_jsons(self.thorough_graph)
        reconstituted = from_cx_jsons(graph_cx_str)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False)

    @unittest.skipUnless(NDEX_USERNAME in os.environ and NDEX_PASSWORD in os.environ, 'Need NDEx credentials')
    def test_thorough_ndex(self):
        """Tests that a document can be uploaded and downloaded. Sleeps in the middle so that NDEx can process"""
        network_id = to_ndex(self.thorough_graph)
        time.sleep(10)
        reconstituted = from_ndex(network_id)

        do_remapping(self.thorough_graph, reconstituted)

        self.bel_thorough_reconstituted(reconstituted, check_warnings=False, check_citation_name=False)

    def test_thorough_upgrade(self):
        lines = to_bel_lines(self.thorough_graph)
        reconstituted = from_lines(lines, manager=self.manager)
        self.bel_thorough_reconstituted(reconstituted, check_citation_name=False)

    def test_slushy(self):
        self.bel_slushy_reconstituted(self.slushy_graph)

    def test_slushy_bytes(self):
        graph_bytes = to_bytes(self.slushy_graph)
        graph = from_bytes(graph_bytes)
        self.bel_slushy_reconstituted(graph)

    def test_slushy_syntax_errors(self):
        syntax_errors = get_syntax_errors(self.slushy_graph)
        self.assertEqual(1, len(syntax_errors))
        self.assertEqual(98, syntax_errors[0][0])

    def test_slushy_json(self):
        graph_json = to_json(self.slushy_graph)
        graph = from_json(graph_json)
        self.bel_slushy_reconstituted(graph)

    def test_slushy_graphml(self):
        handle, path = tempfile.mkstemp()

        with open(path, 'wb') as f:
            to_graphml(self.slushy_graph, f)

        os.close(handle)
        os.remove(path)

    def test_slushy_cx(self):
        reconstituted = from_cx(to_cx(self.slushy_graph))

        do_remapping(self.slushy_graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)

    def test_slushy_cxs(self):
        reconstituted = from_cx_jsons(to_cx_jsons(self.slushy_graph))

        do_remapping(self.slushy_graph, reconstituted)

        self.bel_slushy_reconstituted(reconstituted)

    def test_simple_compile(self):
        self.bel_simple_reconstituted(self.simple_graph)

    def test_simple_cx(self):
        """Tests the CX input/output on test_bel.bel"""
        graph_cx_json = to_cx(self.simple_graph)

        reconstituted = from_cx(graph_cx_json)
        do_remapping(self.simple_graph, reconstituted)

        self.bel_simple_reconstituted(reconstituted)

    def test_isolated_compile(self):
        self.bel_isolated_reconstituted(self.isolated_graph)

    @mock_bel_resources
    def test_isolated_upgrade(self, mock):
        lines = to_bel_lines(self.isolated_graph)
        reconstituted = from_lines(lines, manager=self.manager)
        self.bel_isolated_reconstituted(reconstituted)

    @mock_bel_resources
    def test_misordered_compile(self, mock):
        """This test ensures that non-citation clearing mode works"""
        self.assertEqual(4, self.misordered_graph.number_of_nodes())
        self.assertEqual(3, self.misordered_graph.number_of_edges())

        e1 = {
            RELATION: INCREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assertHasEdge(self.misordered_graph, AKT1, EGFR, **e1)

        e2 = {
            RELATION: DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assertHasEdge(self.misordered_graph, EGFR, FADD, **e2)

        e3 = {
            RELATION: DIRECTLY_DECREASES,
            CITATION: citation_1,
            EVIDENCE: evidence_1,
            ANNOTATIONS: {
                'TESTAN1': {testan1: True}
            }
        }
        self.assertHasEdge(self.misordered_graph, EGFR, CASP8, **e3)


namespaces = {
    'TESTNS': {
        "1": "GRP",
        "2": "GRP"
    }
}

annotations = {
    'TestAnnotation1': {'A', 'B', 'C'},
    'TestAnnotation2': {'X', 'Y', 'Z'},
    'TestAnnotation3': {'D', 'E', 'F'}
}


class TestFull(TestTokenParserBase):
    @classmethod
    def setUpClass(cls):
        cls.graph = BELGraph()
        cls.parser = BelParser(
            cls.graph,
            namespace_dict=namespaces,
            annotation_dict=annotations,
            namespace_regex={'dbSNP': 'rs[0-9]*'}
        )

    def test_regex_match(self):
        line = 'g(dbSNP:rs10234) -- g(dbSNP:rs10235)'
        self.add_default_provenance()
        self.parser.parseString(line)
        self.assertIn((GENE, 'dbSNP', 'rs10234'), self.parser.graph)
        self.assertIn((GENE, 'dbSNP', 'rs10235'), self.parser.graph)

    def test_regex_mismatch(self):
        line = 'g(dbSNP:10234) -- g(dbSNP:rr10235)'

        with self.assertRaises(MissingNamespaceRegexWarning):
            self.parser.parseString(line)

    def test_semantic_failure(self):
        statement = "bp(TESTNS:1) -- p(TESTNS:2)"
        with self.assertRaises(InvalidFunctionSemantic):
            self.parser.parseString(statement)

    def test_missing_citation(self):
        statements = [
            test_set_evidence,
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        with self.assertRaises(MissingCitationException):
            self.parser.parse_lines(statements)

    def test_annotations(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = "A"',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]

        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.graph.number_of_nodes())
        self.assertTrue(self.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.graph.has_node_with_data(test_node_2_dict))

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True},
                'TestAnnotation2': {'X': True},
            },
            EVIDENCE: test_evidence_text,
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_with_list(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_2_dict))

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True}
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)

    def test_annotations_with_multilist(self):
        self.add_default_provenance()

        statements = [
            'SET TestAnnotation1 = {"A","B"}',
            'SET TestAnnotation2 = "X"',
            'SET TestAnnotation3 = {"D","E"}',
            'g(TESTNS:1) -> g(TESTNS:2)'
        ]
        self.parser.parse_lines(statements)

        test_node_1_dict = gene(namespace='TESTNS', name='1')
        test_node_2_dict = gene(namespace='TESTNS', name='2')

        test_node_1 = test_node_1_dict.as_tuple()
        test_node_2 = test_node_2_dict.as_tuple()

        self.assertEqual(2, self.parser.graph.number_of_nodes())
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_1_dict))
        self.assertTrue(self.parser.graph.has_node_with_data(test_node_2_dict))

        self.assertEqual(1, self.parser.graph.number_of_edges())

        kwargs = {
            ANNOTATIONS: {
                'TestAnnotation1': {'A': True, 'B': True},
                'TestAnnotation2': {'X': True},
                'TestAnnotation3': {'D': True, 'E': True}
            },
            CITATION: test_citation_dict
        }
        self.assertHasEdge(test_node_1, test_node_2, **kwargs)


class TestRandom(unittest.TestCase):
    def test_import_warning(self):
        """Tests an error is thrown when the version is set wrong"""
        graph = BELGraph()

        # Much with stuff that would normally be set
        graph.graph[GRAPH_PYBEL_VERSION] = '0.0.0'

        graph_bytes = to_bytes(graph)

        with self.assertRaises(ImportVersionWarning) as cm:
            from_bytes(graph_bytes)

            self.assertEqual(
                import_version_message_fmt.format('0.0.0', PYBEL_MINIMUM_IMPORT_VERSION),
                str(cm.exception)
            )


if __name__ == '__main__':
    unittest.main()
