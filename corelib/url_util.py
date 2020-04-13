import requests
import urllib.parse


def precheck_url(original_url):
    '''
    Performs a quick precheck on the format of the url
    '''
    if original_url is None or len(original_url) == 0:
        return False
    return True


def adjust_url(original_url):
    '''
    Return adjusted url if the url is reachable; otherwise None
    '''
    print('Original URL:', original_url)
    preprocessed_url = original_url.strip()
    preprocessed_url = preprocessed_url.lower()

    working_url = None
    for url_scheme in ['https', 'http']:
        url_parse = urllib.parse.urlparse(preprocessed_url, scheme=url_scheme)
        if url_parse.netloc == '':
            url_parse = url_parse._replace(netloc=url_parse.path)
            url_parse = url_parse._replace(path='')

        candidate_url = urllib.parse.urlunparse(url_parse)
        is_working = test_url(candidate_url)
        print('url_scheme='+url_scheme, 'candidate_url='+candidate_url,
              'candidate_url_components='+str(url_parse), 'is_working='+str(is_working))
        if is_working:
            working_url = candidate_url
            break

    return working_url


def test_url(url):
    '''
    Return True if url is reachable; otherwise False
    Try head request first; if failed, then try get request
    '''
    header_list = [{'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.92 Safari/537.36'}, 
                    dict()]
    
    for request_func in [requests.head, requests.get]:
        for header in header_list:
            try:
                r = request_func(url=url, timeout=2, headers=header)
                
                # print(r, url, request_func.__name__, header)
                
                if r.status_code == 200:
                    return True
            except Exception:
                pass

    return False