

def merge_update(dst, src):

    for k, v in src.iteritems():

        if k not in dst:
            dst[k] = v
            continue

        e = dst[k]
        if isinstance(e, dict):
            merge_update(e, v)
        elif isinstance(e, list):
            e.extend(v)
        else:
            dst[k] = v

