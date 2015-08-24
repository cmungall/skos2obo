#!/usr/bin/env python3

__author__ = 'cjm'

import argparse
import logging
import requests
import sys
import os
import yaml

import rdflib
from rdflib import Namespace
from rdflib.namespace import RDF
from rdflib.namespace import SKOS

GEMET = Namespace('http://www.eionet.europa.eu/gemet/2004/06/gemet-schema.rdf#')

g = rdflib.Graph()
lang = 'en'

rprefixmap = {}

def main():
    parser = argparse.ArgumentParser(description='skos2obo'
                                                 'Hacky converter for skos to obo',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--input', type=str, required=False,
                        help='Input metadata file')
    parser.add_argument('-n', '--name', type=str, required=False, default='foo',
                        help='Ontology name')
    parser.add_argument('-p', '--prefixes', type=str, required=False,
                        help='Prefix map yaml file')

    parser.add_argument('files',nargs='*')
    args = parser.parse_args()

    prefixmap = {}
    if (args.prefixes):
        f = open(args.prefixes, 'r') 
        prefixmap = yaml.load(f)

    for k,v in prefixmap.items():
        rprefixmap[v] = k

    for file in args.files:
        g.parse(file)
    process_graph(g, args.name)


def uri2id(uri):
    s = "{:s}".format(str(uri))
    for uribase,prefix in rprefixmap.items():
        if (s.startswith(uribase)):
            s = s.replace(uribase,prefix+":")
    return s

def process_graph(g, ont_id):
    print("ontology: {:s}".format(ont_id))
    smap = {}
    for concept in g.subjects(RDF.type, SKOS.Concept):
        for s in get_schemes(g,concept):
            smap[uri2id(s)] = s
    for s,c in smap.items():
        print('subsetdef: {:s} "{:s}"'.format(s, get_label(g,c)))
    print("")
    for concept in g.subjects(RDF.type, SKOS.Concept):
        concept_uri = str(concept)

        print("[Term]")
        print("id: " + uri2id(concept))
        print("name: {:s}".format(get_label(g,concept)))
        for defn in g.objects(concept, SKOS.definition):
            if (defn.language == lang):
                print('def: "{:s}" [{:s}]'.format(defn.value, concept_uri))
        for s in g.objects(concept, SKOS.broader):
            print('is_a: {:s} ! {:s}'.format(uri2id(s), get_label(g,s)))
        for m in g.objects(concept, SKOS.exactMatch):
            print('xref: {:s}'.format(uri2id(m)))
        for s in get_schemes(g,concept):
            print('subset: {:s}'.format(uri2id(s)))
        print("")

def get_schemes(g,concept):
    return list(g.objects(concept, GEMET.group)) + list(g.objects(concept, SKOS.inScheme))

def get_label(g,concept):
    labels = sorted(g.preferredLabel(concept, lang=lang))
    if (len(labels) == 0):
        return ""
    return labels[0][1].value



if __name__ == "__main__":
    main()
