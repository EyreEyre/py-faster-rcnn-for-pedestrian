#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------
# caltech_vbb
# Copyright (c) 2017 Zhewei Xu
# Licensed under The MIT License [see LICENSE for details]
# --------------------------------------------------------

from scipy.io import loadmat
from collections import defaultdict
import json
import glob
import os
import math

def load_vbb(filename):
    '''
    A is a dict load from the caltech vbb file has the same data structure.
    '''
    vbb = loadmat(filename)
    nFrame = int(vbb['A'][0][0][0][0][0])
    objLists = vbb['A'][0][0][1][0]
    maxObj = int(vbb['A'][0][0][2][0][0])
    objInit = vbb['A'][0][0][3][0]
    objLbl = [str(v[0]) for v in vbb['A'][0][0][4][0]]
    objStr = vbb['A'][0][0][5][0]
    objEnd = vbb['A'][0][0][6][0]
    objHide = vbb['A'][0][0][7][0]
    altered = int(vbb['A'][0][0][8][0][0])
    log = vbb['A'][0][0][9][0]
    logLen = int(vbb['A'][0][0][10][0][0])
    
    obj_list = defaultdict(dict)
    for frame_id, obj in enumerate(objLists):
        objs = []
        if len(obj) > 0:
            for id, pos, occl, lock, posv in zip(obj['id'][0], obj['pos'][0], obj['occl'][0], obj['lock'][0], obj['posv'][0]):
                id = int(id[0][0])-1 # matlab is 1-start
                pos = pos[0].tolist()
                occl = int(occl[0][0])
                lock = int(lock[0][0])
                posv = posv[0].tolist()
                keys_obj = ('id','pos','occl','lock','posv','ignore')
                datum = dict(zip(keys_obj, [id, pos, occl, lock, posv, False]))
                datum['lbl'] = objLbl[id]
                objs.append(datum)
        obj_list[frame_id+1] = objs
    
    keys_vbb = ('nFrame','objLists','maxObj','objInit','objLbl','objStr','objEnd','objHide','altered','log','logLen')
    A = dict(zip(keys_vbb, [nFrame, obj_list, maxObj, objInit, objLbl, objStr, objEnd, objHide, altered, log, logLen]))
    return A

def get_caltech_annoations(image_identifiers, ann_dir, param={}):
    '''
    get all image_identifiers annotation

    INPUTS:
        image_identifiers   - a list contaions image identifier like 'set00/V000/1'
        ann_dir             - 
        param               -
    OUPUT:
        anno : {'set00/V000/121': [{'id': 3,
                                    'lbl': 'person',
                                    'lock': 0,
                                    'occl': 1,
                                    'pos': [230.68536627473338,131.379092381353,7.045344709775236,13.1208549490851],
                                    'posv': [230.68536627473338,131.379092381353,7.045344709775236,13.1208549490851]}],
                                    ...
                }
    '''
    anno = {}
    data = defaultdict(dict)
    for dname in sorted(glob.glob(ann_dir+'/set*')):
        set_name = os.path.basename(dname)
        data[set_name] = defaultdict(dict)
        for anno_fn in sorted(glob.glob('{}/*.vbb'.format(dname))):
            vid_anno = load_vbb(anno_fn)
            video_name = os.path.splitext(os.path.basename(anno_fn))[0]
            data[set_name][video_name] = vid_anno['objLists']
            
    for image_identifier in image_identifiers:
        image_set_name = image_identifier[0:5]
        image_seq_name = image_identifier[6:10]
        image_id       = int(image_identifier[11:])
        #Tracer()()
        if image_id in data[image_set_name][image_seq_name]:
            #Tracer()()
            if len(param)!=0:
                #Tracer()()
                anno[image_identifier] = bbox_filter(data[image_set_name][image_seq_name][image_id],param)
            else:
                anno[image_identifier] = data[image_set_name][image_seq_name][image_id]
        else:
            print "Warning: No %s.jpg found in annotations" %(image_identifier)
           
        #vis_annotations(image_identifier, anno[image_identifier])
    return anno

def get_image_identifiers(imageSets_file):
    '''get image identifiers from ImageSets dir's file for train or test. like {'set00/V000/1','set/V000/31'...}'''
    with open(imageSets_file, 'r') as f:
        lines = f.readlines()
    image_identifiers = [x.strip() for x in lines]

    return image_identifiers

def bbox_filter(bboxs,param):
    '''
    Filter bbox by param.

    Param is a dictionary containing some filter conditions. The conditions please see get_default_filter().

    bbox which not in param['lbls'] or param['ilbls'] would excluded.
    bbox wihch dose not meet other param, bbox['ignore'] would set True.

    USEAGE
        bbox_filter(bboxs,param)
            
    INPUT
        param       - a dict created by get_default_filter()
        bboxs       - a list contains bbox annotations
    
    OUPUT
        bbox_filted - a list contains filted bbox
    
    EXAMPLE
        bboxs = list(recs('set00/V000/1'))
        param=get_default_filter()
        param['lbls']=['person']
        param['ilbls']=['people']
        param['squarify']=[3,0.41]
        param['hRng']=[50,float('inf')]
        param['vRng']=[1,1]
        bbox_filter(bboxs,param)
    
    See also get_default_filter(), bbox_squarify(), bbox_resize()
    '''
    # Tracer()()
    n = len(bboxs)
    bbox_filted = []
    
    if len(param['lbls']) != 0:
        lbl = set(param['lbls'])|(set(param['ilbls'])) 
        for i in range(n):            
            if bboxs[i]['lbl'] in lbl:
                bbox_filted.append(bboxs[i])
    
    for i in range(len(bbox_filted)):
        # Tracer()()
        if len(param['ilbls']) != 0:
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or (bbox_filted[i]['lbl'] in param['ilbls'])
        if len(param['xRng']) != 0:
            v = bboxs[i]['pos'][0]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['xRng'][0] or v > param['xRng'][1]
            v = bbox_filted[i]['pos'][0] + bbox_filted[i]['pos'][2]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['xRng'][0] or v > param['xRng'][1]
        if len(param['yRng']) != 0:
            v = bbox_filted[i]['pos'][1]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['yRng'][0] or v > param['yRng'][1]
            v = bbox_filted[i]['pos'][1] + bbox_filted[i]['pos'][3]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['yRng'][0] or v > param['yRng'][1]
        if len(param['wRng']) != 0:
            v = bbox_filted[i]['pos'][2]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['wRng'][0] or v > param['wRng'][1]
        if len(param['hRng']) != 0:
            v = bbox_filted[i]['pos'][3]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['hRng'][0] or v > param['hRng'][1]
        if len(param['aRng']) != 0:
            v = bbox_filted[i]['pos'][2] * bbox_filted[i]['pos'][3]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['aRng'][0] or v > param['aRng'][1]
        if len(param['arRng']) != 0:
            v = bbox_filted[i]['pos'][2] / bbox_filted[i]['pos'][3]
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['arRng'][0] or v > param['arRng'][1]
        if len(param['vRng']) != 0:
            pos  = bbox_filted[i]['pos']
            posv = bbox_filted[i]['posv']
            if bbox_filted[i]['occl']==0 or set(posv)=={0}:
                v = 1
            elif cmp(posv,pos):
                v = 0
            else:
                v = (posv[2]*posv[3])/(pos[2]*pos[3])
            bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or v < param['vRng'][0] or v > param['vRng'][1]
        if len(param['occl']) != 0:
            '''occl= 0|1|2 represent for no occl | occl | no and occl'''
            if param['occl'] != 2:
                bbox_filted[i]['ignore'] = bbox_filted[i]['ignore'] or (bbox_filted[i]['occl'] != param['occl'])
        if (bbox_filted[i]['ignore'] == 0) and (len(param['squarify']) != 0):
            bbox_filted[i]['pos'] = bbox_squarify(bbox_filted[i]['pos'],param['squarify'][0],param['squarify'][1])
        # Tracer()()
    # Tracer()()
    return bbox_filted

def bbox_squarify(bb,flag,ar=1):
    '''
    Fix bb aspect ratios (without moving the bb centers).
    Reimplimentation of bbGt('squarify) from Piotr's CV matlab toolbox.
    
    The w or h of each bb is adjusted so that w/h=ar.
    The parameter flag controls whether w or h should change:
    flag==0: expand bb to given ar
    flag==1: shrink bb to given ar
    flag==2: use original w, alter h
    flag==3: use original h, alter w
    flag==4: preserve area, alter w and h
    If ar==1 (the default), always converts bb to a square, hence the name.

    USAGE
    bbr = squarify(bb, flag, [ar])

    INPUTS
    bb     - [nx4] original bbs
    flag   - controls whether w or h should change
    ar     - [1] desired aspect ratio

    OUTPUT
    bbr    - the output 'squarified' bbs

    EXAMPLE
    bbr = squarify([0 0 1 2],0)

    See also bbApply, bbApply>resize
    '''
    # Tracer()()
    bbr=list(bb)
    if flag == 4:
        bbr = bbox_resize(bb,0,0,ar)
        return bbr
    usew = (flag == 0 and (bb[2]>bb[3]*ar)) or (flag == 1 and (bb[2]<bb[3]*ar)) or flag == 2
    if usew:
        bbr = bbox_resize(bb,0,1,ar)
    else:
        bbr = bbox_resize(bb,1,0,ar)
        
    return bbr

def bbox_resize(bb,hr,wr,ar=0):
    '''
    Resize the bbs (without moving their centers).

    If wr>0 or hr>0, the w/h of each bb is adjusted in the following order:
        if hr!=0: h=h*hr
        if wr1=0: w=w*wr
        if hr==0: h=w/ar
        if wr==0: w=h*ar
    Only one of hr/wr may be set to 0, and then only if ar>0. If, however,
    hr=wr=0 and ar>0 then resizes bbs such that areas and centers are
    preserved but aspect ratio becomes ar.

    USAGE
        bb = ( resize, bb, hr, wr, [ar] )

    INPUTS
        bb     - [nx4] original bbs
        hr     - ratio by which to multiply height (or 0)
        wr     - ratio by which to multiply width (or 0)
        ar     - [0] target aspect ratio (used only if hr=0 or wr=0)

    OUTPUT
        bb    - [nx4] the output resized bbs

    EXAMPLE
        bb = resize([0 0 1 1],1.2,0,.5) % h'=1.2*h; w'=h'/2;

    See also bbApply, bbApply>squarify
    '''
    # Tracer()()
    assert len(bb)==4
    assert (hr>0 and wr>0) or ar>0
    if hr==0 and wr==0:
        a = math.sqrt(bb[2]*bb[3])
        ar= math.sqrt(ar)
        d = a*ar - bb[2]; bb[0]=bb[0]-d/2; bb[2]=bb[2]+d
        d = a*ar - bb[3]; bb[1]=bb[1]-d/2; bb[3]=bb[3]+d
        return bb
    if hr!=0:
        d=(hr-1)*bb[3]; bb[1]=bb[1]-d/2; bb[3]=bb[3]+d
    if wr!=0:
        d=(hr-1)*bb[2]; bb[0]=bb[0]-d/2; bb[2]=bb[2]+d
    if hr==0:
        d=bb[2]/ar-bb[3]; bb[1]=bb[1]-d/2; bb[3]=bb[3]+d
    if wr==0:
        d=bb[3]*ar-bb[2]; bb[0]=bb[0]-d/2; bb[2]=bb[2]+d
    
    return bb

def get_default_filter():
    df = dict()
    df['format']  = 0
    df['ellipse'] = 1
    df['squarify']= []
    df['lbls']    = []
    df['ilbls']   = []
    df['hRng']    = []
    df['wRng']    = []
    df['aRng']    = []
    df['arRng']   = []
    df['oRng']    = []
    df['xRng']    = []
    df['yRng']    = []
    df['vRng']    = []
    df['occl']    = []
    df['squarify'] = []
    
    return df

def get_image_identifiers(imageSets_file):
    '''get image identifiers like {'set00/V000/1','set00/V000/2',...}'''
    with open(imageSets_file, 'r') as f:
        lines = f.readlines()
    image_identifiers = [x.strip() for x in lines]
    return image_identifiers



def get_param_default(var,df):
    pass


def num_obj(self, A):
    pass

def frame_ann(self, A, frame, lbls, test):
    # no need for now
    return 0

def bbox_load(self, filename, pLoad=None):
    pass

def is_empty(input_object):
    return (input_object is None) or (len(input_object) == 0)


def save_vbb():
    pass


def load_txt(filename):
    '''
    load annotation from caltech vbb txt file.
    unfinish
    '''
    A = {}
    vbb = open(filename)
    lines = vbb_file.readlines()
    for line_n in range(len(lines)):
        line = lines[line_n]
        line_n = line_n + 1
        vbb_data = dict(re.findall(r'([A-Za-z]*)=[\']*(\[.*\]|[^\[\]\s\']*)[\']*',line))

        if 'nFrame' in vbb_data:
            nFrame = int(vbb_data['nFrame'])
        if 'lbl' in vbb_data:
            lbl = vbb_data['lbl']

            start = int(vbb_data['str'])
            end = int(vbb_data['end'])
            hide = int(vbb_data['hide'])

            line = lines[line_n]
            line_n = line_n + 1
            pos = re.findall(r'([0-9\.]+)',line)

            line = lines[line_n]
            line_n = line_n + 1
            posv = re.findall(r'([0-9\.]+)',line)

            line = lines[line_n]
            line_n = line_n + 1
            occl = re.findall(r'([0-9\.]+)',line)

            line = lines[line_n]
            line_n = line_n + 1
            lock = re.findall(r'([0-9\.]+)',line)
    return A

def load_json(filename):
    A = json.open(filename)
    pass

def save_json():
    pass

def get_anno():
    pass