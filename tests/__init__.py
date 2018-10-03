from bs4 import BeautifulSoup
from upload.database import db

def login(client, faker):
    u = faker.user_details()
    db.session.add(u)
    db.session.commit()

    resp = client.get('/login')
    soup = BeautifulSoup(resp.data, 'html.parser')

    crf_token = soup.find(
        'input',
        {'name': 'csrf_token'},
        type='hidden',
        id='csrf_token',
    )

    data = dict(
        email=u.email,
        password=u.password,
    )

    if crf_token:
        data['csrf_token'] = crf_token.get('value')

    client.post('/login', data=data, follow_redirects=True)

    return u
