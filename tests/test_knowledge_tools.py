from agentic.tools.knowledge_tools import search_knowledge_base


def test_search_knowledge_base_returns_correct_article_as_top_result():
    results = search_knowledge_base("login")
    assert results[0]["title"] == "How to Handle Login Issues?"
    assert results[0]["confidence"] > 0.4


def test_search_knowledge_base_ranks_stronger_match_higher():
    results = search_knowledge_base("refund")
    assert results[0]["title"] == "How to Request a Refund"
    assert results[0]["confidence"] > results[1]["confidence"] > 0


def test_search_knowledge_base_natural_language_question_still_matches():
    results = search_knowledge_base("What's included in my CultPass subscription?")
    assert results[0]["title"] == "What's Included in a CultPass Subscription"
    assert results[0]["confidence"] > 0


def test_search_knowledge_base_no_match():
    results = search_knowledge_base("completely unrelated nonsense query xyz123")
    assert results == []
