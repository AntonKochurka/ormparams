from ormparams.rules import ParserRules
from ormparams.parser import Parser

q_def = "profile@username__contains=foo&age__gt=30"
q_alt = "profile.username--contains=foo&age--gt=30"

r_def = ParserRules()
r_alt = ParserRules(
    suffix_delimiter="--", relationships_delimiter=".", unknown_suffix_reaction="warn"
)

p_def = Parser(r_def)
p_alt = Parser(r_alt)

_ = p_def.parse_url(q_def) == p_alt.parse_url(q_alt)
print(_)
assert _ is True
