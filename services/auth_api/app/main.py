from fastapi import FastAPI

app = FastAPI(title='tof_local_knowledge_auth_api', version='0.1.0')


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'auth_api'}


@app.get('/roles')
def roles():
    return {
        'roles': [
            'system_admin',
            'source_admin',
            'knowledge_user',
            'auditor',
            'service_account',
        ]
    }
