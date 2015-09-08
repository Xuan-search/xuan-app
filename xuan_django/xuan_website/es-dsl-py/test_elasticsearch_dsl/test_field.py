from elasticsearch_dsl import field


def test_field_from_dict():
    f = field.construct_field({'type': 'string', 'index': 'not_analyzed'})

    assert isinstance(f, field.String)
    assert {'type': 'string', 'index': 'not_analyzed'} == f.to_dict()


def test_multi_fields_are_accepted_and_parsed():
    f = field.construct_field(
        'string',
        fields={
            'raw': {'type': 'string', 'index': 'not_analyzed'},
            'eng': field.String(analyzer='english'),
        }
    )

    assert isinstance(f, field.String)
    assert {
        'type': 'string',
        'fields': {
            'raw': { 'type': 'string', 'index': 'not_analyzed'},
            'eng': { 'type': 'string', 'analyzer': 'english'},
        }
    } == f.to_dict()

def test_modifying_nested():
    f = field.Nested()
    f.field('name', 'string', index='not_analyzed')

    assert {
        'type': 'nested',
        'properties': {
            'name': {'type': 'string', 'index': 'not_analyzed'}
        },
    } == f.to_dict()

def test_nested_provides_direct_access_to_its_fields():
    f = field.Nested()
    f.field('name', 'string', index='not_analyzed')

    assert 'name' in f
    assert f['name'] == field.String(index='not_analyzed')


def test_field_supports_multiple_analyzers():
    f = field.String(index_analyzer='snowball', search_analyzer='keyword')
    assert {'index_analyzer': 'snowball', 'search_analyzer': 'keyword', 'type': 'string'} == f.to_dict()


def test_multifield_supports_multiple_analyzers():
    f = field.String(fields={
        'f1': field.String(search_analyzer='keyword', index_analyzer='snowball'),
        'f2': field.String(analyzer='keyword')
    })
    assert {
       'fields': {
           'f1': {'index_analyzer': 'snowball',
                  'search_analyzer': 'keyword',
                  'type': 'string'
           },
           'f2': {
               'analyzer': 'keyword', 'type': 'string'}
       },
       'type': 'string'
    } == f.to_dict()
