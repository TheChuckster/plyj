#!/usr/bin/env python2

import sys
from plyplus.strees import STree
import parser as plyj

import logging
logger = logging.getLogger('parser_log')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def java_ply_adapter(tree):  # uses PLYj methods to construct a Ply STree data structure from the PLYj parser result
    if tree is None or isinstance(tree, str) or isinstance(tree, int) or isinstance(tree, dict):
        return None

    tail = []
    for param_name in tree._fields:
        param = getattr(tree, param_name)
        if isinstance(param, list):
            tail.extend(filter(None, map(java_ply_adapter, param)))
        else:
            tail_node = java_ply_adapter(param)
            if tail_node is not None:
                assert isinstance(tail_node, STree)
                tail.append(tail_node)

    adapted_tree = STree(tree.__class__.__name__, tail, tree.lineno if hasattr(tree, 'lineno') else set())
    adapted_tree.original_nodes = tree
    if hasattr(tree, 'value') and hasattr(tree, 'name'):
        adapted_tree.label = str(tree.name) + ':' + str(tree.value)
    elif hasattr(tree, 'name'):
        adapted_tree.label = str(tree.name)
    elif hasattr(tree, 'value'):
        adapted_tree.label = str(tree.value)

    return adapted_tree


def print_tree(node, level=0, **kwargs):
    if not node:
        return
    elif not hasattr(node, 'head'):
        print_output = level*'  ' + str(node)
        if 'logging' in kwargs and kwargs['logging']:
            logger.debug(print_output)
        else:
            print print_output
    else:  # has to have head
        print_output = level*'  ' + str(node.head) + ((' ('+node.label+')') if hasattr(node, 'label') else '') + ((':' + str(node.hash['lineno'])) if hasattr(node, 'hash') else ((':' + str(node.lineno)) if hasattr(node, 'lineno') else '')) + ((':' + str(node.lexpos)) if hasattr(node, 'lexpos') else '')
        if hasattr(node, 'parent') and node.parent and hasattr(node.parent, 'head'):
            print_output += (' --> ' + str(node.parent.head))

        if 'logging' in kwargs and kwargs['logging']:
            logger.debug(print_output)
        else:
            print print_output

        if hasattr(node, 'tail'):
            for n in node.tail:
                if n != node:
                    print_tree(n, level + 1, **kwargs)


def add_parents(node, parent=None):
    # first check head and return None -- remember nodes that are
    if not node or not hasattr(node, 'tail'):
        return node  # may want to preserve non-nodes

    node.parent = parent  # can be None
    node.tail = filter(None, map(lambda x: add_parents(x, node) if x != node else x, node.tail))
    return node


def bottom_up_map(node, fn):
    if node:
        # get to bottom
        if not hasattr(node, 'tail') or (len(node.tail) == 0):  # leaf! start mapping up
            map_traverse_up(node, fn)
        else:
            for n in node.tail:
                bottom_up_map(n, fn)


def map_traverse_up(node, fn, child_node=None):
    if not node:
        return

    node = fn(node, child_node)  # so apply LAST node's child node to this one

    if hasattr(node, 'parent') and node.parent:
        map_traverse_up(node.parent, fn, node)  # now call this with the parent node but pass in the node as the child node


def lineno_mapper(node, child):
    if node is None or child is None:  # SUBTLETY: have to return node instead of None here to ensure we're not clobbing nodes with no children!
        return node

    if hasattr(node, 'lineno') and hasattr(child, 'lineno'):
        node.lineno |= child.lineno

    return node


def main():
    if len(sys.argv) == 1:
        print('''usage: parse_expr.py <filename> ...
       Example: parse_expr.py Hello.java Hello2.java ''')
        sys.exit(1)

    parser = plyj.Parser()
    for filename in sys.argv[1:]:
        parsed = parser.parse_file(filename)
        
        # logger.debug(parsed)
        # print(parsed.__dict__)
        
        t = java_ply_adapter(parsed)
        t = add_parents(t)
        bottom_up_map(t, lambda x, y: lineno_mapper(x, y))
        print_tree(t, logging=True)

if __name__ == "__main__":
    main()
