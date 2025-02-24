from requests import get as requests_get

def test_findings():
    response = requests_get('http://spt-apiserver-testing-apiserver:8080/findings/?study=Melanoma+intralesional+IL2')
    if response.status_code != 200:
        print(response)
        print(response.reason)
        print(response.text)
        raise ValueError(f'Request not OK. HTTP {response.status_code}')
    print(response.json())

if __name__=='__main__':
    test_findings()
