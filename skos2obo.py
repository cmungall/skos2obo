#!/usr/bin/env python3

__author__ = 'cjm'

import argparse
import logging
import requests
import sys
import os

import rdflib
from rdflib import Namespace
from rdflib.namespace import RDF
from rdflib.namespace import SKOS

GEMET = Namespace('http://www.eionet.europa.eu/gemet/2004/06/gemet-schema.rdf#')

g = rdflib.Graph()
lang = 'en'

# prints graph has 79 statements.

termdict = dict()
groupdict = dict()



def main():
    parser = argparse.ArgumentParser(description='skos2obo'
                                                 'Hacky converter for skos to obo',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--input', type=str, required=False,
                        help='Input metadata file')

    parser.add_argument('files',nargs='*')
    args = parser.parse_args()
    for file in args.files:
        print("parsing "+file)
        g.parse(file)
    process_graph(g)
    write_ontology()

def get_term(id):
    if id in termdict:
        return termdict[id]
    else:
        termdict[id] = dict()
        termdict[id]['id'] = id
        return termdict[id]

def get_subset(id):
    n = get_term(id)['label']
    return n.replace(" ","_").replace(",","").replace("(","").replace(")","")

def uri2id(uri):
    return str(uri)

def process_graph(g):
    for concept in g.subjects(RDF.type, SKOS.Concept):
        concept_uri = str(concept)

        print("[Term]")
        print("id: " + uri2id(concept))
        print("name: {:s}".format(get_label(g,concept)))
        for defn in g.objects(concept, SKOS.definition):
            if (defn.language == lang):
                print('def: "{:s}" [{:s}]'.format(defn.value, concept_uri))
        for s in g.objects(concept, SKOS.broader):
            print('is_a: {:s} ! {:s}'.format(uri2id(s), get_label(g,concept)))
        for m in g.objects(concept, SKOS.exactMatch):
            print('xref: {:s}'.format(uri2id(m)))
        for grp in get_schemes(g,concept):
            print('subset: {:s}'.format(uri2id(m)))
        print("")

def get_schemes(g,concept):
    return list(g.objects(concept, GEMET.group)) + list(g.objects(concept, SKOS.inScheme))

def get_label(g,concept):
    return sorted(g.preferredLabel(concept, lang=lang))[0][1].value
    
def old_process_graph(g):
    for subj1, pred1, obj1 in g:
        # hack!
        subj = str(subj1)
        obj = str(obj1)
        pred = str(pred1)
        if pred == 'http://www.w3.org/2004/02/skos/core#prefLabel':
            get_term(subj)['label'] = obj
        elif pred == 'http://www.w3.org/2000/01/rdf-schema#label':
            get_term(subj)['label'] = obj
        elif pred == 'http://www.w3.org/2004/02/skos/core#broader':
            get_term(subj)['is_a'] = obj
        elif pred == 'http://www.w3.org/2004/02/skos/core#definition':
            get_term(subj)['definition'] = obj
        elif pred == 'http://www.eionet.europa.eu/gemet/2004/06/gemet-schema.rdf#group':
            get_term(subj)['group'] = obj
            groupdict[obj] = 1

def write_ontology():
    print("ontology: gemet")
    for k in groupdict:
        n = get_subset(k)
        print('subsetdef: '+n+' "' + n + '"')
    print("")

    for k in termdict:
        write_stanza(termdict[k])

def write_stanza(obj):
    if obj['id'] in groupdict:
        return
    print("[Term]")
    print("id: "+obj['id'])
    if ('label' in obj):
        print("name: "+obj['label'])
    if ('is_a' in obj):
        print("is_a: "+obj['is_a'])
    if ('group' in obj):
        print("subset: "+get_subset(obj['group']))
    if ('definition' in obj):
        defn = obj['definition'].replace("\n"," ").replace("\"","'")
        print("def: \""+defn+"\" []")
    print("")


if __name__ == "__main__":
    main()
