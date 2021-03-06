from js9 import j
import copy

JSBASE = j.application.jsbase_get_class()
class SerializerDict(JSBASE):

    def __init__(self):
        JSBASE.__init__(self)

    def _unique_list(self, items, sort=False, strip=False):
        res = []
        for item in items:
            if strip and j.data.types.string.check(item):
                item = item.strip()
            if item not in res:
                res.append(item)
        if sort:
            res.sort()
        return res

    def set_value(self, dictsource, key, val, add_non_exist=False, die=True, errors=[], listunique=False, listsort=True, liststrip=True):
        """
        start from a dict template (we only go 1 level deep)

        will check the type & corresponding the type fill in

        @return dict,errors=[]

        in errors is list of list [[key,val],...]

        """
        if key not in dictsource.keys():
            if add_non_exist:
                dictsource[key] = val
                return dictsource, errors
            else:
                if die:
                    raise j.exceptions.Input(
                        "dictsource does not have key:%s, can insert value" % key)
                else:
                    errors.append((key, val))
                    return dictsource, errors

        if j.data.types.list.check(dictsource[key]):
            # check is list & set the types accordingly
            if j.data.types.string.check(val):
                if "," in val:
                    val = [item.replace("'", "").strip()
                           for item in val.split(",")]
                else:
                    val = [val]
            elif j.data.types.int.check(val) or j.data.types.float.check(val):
                val = [val]

            if listunique:
                dictsource[key] = self._unique_list(
                    val, sort=listsort, strip=liststrip)
            else:
                dictsource[key] = val

        elif j.data.types.bool.check(dictsource[key]):
            if str(val).lower() in ['true', "1", "y", "yes"]:
                val = True
            else:
                val = False
            dictsource[key] = val
        elif j.data.types.int.check(dictsource[key]):
            if j.data.types.string.check(val) and val.strip() == "":
                val = 0
            dictsource[key] = int(val)
        elif j.data.types.float.check(dictsource[key]):
            dictsource[key] = float(val)
        elif j.data.types.string.check(dictsource[key]):
            dictsource[key] = j.data.text.strip(str(val))
        else:
            raise RuntimeError("could not find type of:%s" % dictsource[key])

        return dictsource, errors

    def merge(self, dictsource={}, dictupdate={}, keys_replace={}, add_non_exist=False, die=True, errors=[], listunique=False, listsort=True, liststrip=True):
        """
        the values of the dictupdate will be applied on dictsource (can be a template)


        @param add_non_exist, if False then will die if there is a value in the dictupdate which is not in the dictsource
        @param keys_replace, key = key to replace with value in the dictsource (which will be the result)
        @param if die=False then will return errors, the list has the keys which were in dictupdate but not in dictsource

        @return dictsource,errors

        """
        if not j.data.types.dict.check(dictsource) or not j.data.types.dict.check(dictupdate):
            raise j.exceptions.Input(
                "dictsource and dictupdate need to be dicts")

        keys = [item for item in dictupdate.keys()]
        keys.sort()

        dictsource = copy.copy(dictsource)  # otherwise template gets changed

        for key in keys:
            val = dictupdate[key]
            if key in keys_replace.keys():
                key = keys_replace[key]
            dictsource, errors = self.set_value(dictsource, key, val, add_non_exist=add_non_exist, die=die,
                                                errors=errors, listunique=listunique, listsort=listsort, liststrip=liststrip)
        return dictsource, errors
