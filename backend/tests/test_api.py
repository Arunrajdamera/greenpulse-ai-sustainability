from fastapi.testclient import TestClient
from app.main import app, analyze, retrieve

client = TestClient(app)

def test_health():
    assert client.get('/health').json()['ai_mode'] == 'Demo AI Mode'

def test_summary_and_trends():
    assert client.get('/api/resources/summary').json()['total_records'] > 100
    assert len(client.get('/api/resources/trends').json()['items']) == 28

def test_analysis_and_recommendations():
    findings = client.post('/api/analyze', json={'resource_type':'Electricity'}).json()['findings']
    assert findings and findings[0]['location'] == 'Block A'
    assert client.post('/api/recommendations', json={'resource_type':'Electricity'}).json()['items']

def test_chat_and_validation():
    chat = client.post('/api/chat', json={'message':'How can we save electricity?'}).json()
    assert chat['sources']
    assert client.post('/api/chat', json={'message':''}).status_code == 422

def test_retrieval_empty_query(): assert retrieve('unrelated zyxw') == []

def test_topic_routing_prioritises_relevant_sources():
    cases = {
        'Why might electricity consumption suddenly increase in a campus building?': 'energy.md',
        'How can a campus reduce water wastage?': 'water.md',
        'How can students reduce paper usage?': 'materials.md',
        'What are good campus recycling practices?': 'materials.md',
        'What is SDG 12?': 'materials.md',
    }
    for question, expected_source in cases.items():
        result_sources = [item['source'] for item in retrieve(question)]
        assert result_sources[0] == expected_source
        assert set(result_sources) == {expected_source}

def test_electricity_chat_is_energy_grounded():
    response = client.post('/api/chat', json={
        'message': 'Why might electricity consumption suddenly increase in a campus building?'
    }).json()
    assert response['sources'][0] == 'energy.md'
    assert 'HVAC' in response['answer']

def test_knowledge_is_grouped_by_document():
    knowledge = client.get('/api/knowledge').json()
    assert knowledge['document_count'] == 3
    assert len(knowledge['items']) == 3
