'''
Created on Feb 2, 2015

@author: torsteinibo
'''

def equalTags(ref1,ref2):
    tags = set()
    for t in ref1.findall("tag"):
        k = t.attrib["k"]
        v = t.attrib["v"]
        if not (k == "source" or k == "source:date"):
            tags.add(k+":"+v)
    
    nTags = 0
    for t in ref2.findall("tag"):
        k = t.attrib["k"]
        v = t.attrib["v"]
        if not (k == "source" or k == "source:date"):
            nTags += 1
            if not (k+":"+v in tags):
                return False
                break
    
    return nTags == len(tags)

def combineWays(fileroot,target,copy):
    if(int(copy.attrib["id"])>0):
        assert(copy.attrib["id"]>0)
    first = True
    for nd in copy.findall("nd"):
        if first:
            first = False
        else:
            target.append(nd)
    if(int(copy.attrib["id"])<0):
        fileroot.remove(copy)
    else:
        copy.attrib["action"]="delete"
    
    if(int(target.attrib["id"])>0):
        target.attrib["action"]="modify"
    
def reLinkRef(relRefs,relations,oldref):
    for ref in relRefs:
        rel = relations[ref]
        mem = rel.findall("member[@ref='%s']" % oldref)
        assert(len(mem)==1)
        rel.remove(mem[0])