from ormparams.core.suffixes import DefaultSuffixSet
from ormparams.core.policy import OrmParamsPolicy
from ormparams.core.parser import OrmParamsParser

from pprint import pprint

policy = OrmParamsPolicy()
parser = OrmParamsParser(policy)

pprint(parser.parse("hello__a=v&hello__b=v&a.b.hello__a__b=v"))
