import sqlparse


def prettify(sql):
    return sqlparse.format(sql, reindent=True, keyword_case='upper')

