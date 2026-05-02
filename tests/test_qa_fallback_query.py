from services.qa_api.app.runtime import fallback_search_query


def test_fallback_search_query_keeps_content_terms():
    assert fallback_search_query('What does the demo say about vacation policy?') == 'demo vacation policy'


def test_fallback_search_query_keeps_negative_test_terms():
    assert fallback_search_query('What is the private customer contract number?') == 'private customer contract number'
