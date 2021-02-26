import ssl
import urllib

ssl._create_default_https_context = ssl._create_unverified_context


def get_file_from_url(url):
    file = urllib.request.urlopen(url)
    return file.read().decode("utf-8")
