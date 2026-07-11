import requests
r = requests.post('http://localhost:8000/api/v1/auth/login', json={'username':'user','password':'user123'})
tok = r.json()['data']['access_token']
h = {'Authorization': f'Bearer {tok}'}
with open(r'D:\traecn\aiskills\7.8\agentflow\test_icon.png','rb') as f:
    r2 = requests.post('http://localhost:8000/api/v1/knowledge/bases/1/icon', headers=h, files={'file': ('test.png', f, 'image/png')})
print('upload:', r2.status_code, r2.text)
