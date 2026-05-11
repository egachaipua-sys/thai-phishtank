
import scripts.content_features as ctnfe
import scripts.url_features as urlfe
import scripts.external_features as trdfe
import tldextract
import requests
import re
import ipaddress
import socket
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import concurrent.futures
import urllib3
import random

key = "ck0c0s80wkgo8gwscc0ookskccs0c4k0c4gs0c0c "



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ---------------------------------------------------------------------------
# SSRF guard
# ---------------------------------------------------------------------------
# The phishing-check endpoint accepts arbitrary user-supplied URLs and fetches
# them server-side. Without this check, an authenticated caller could point us
# at internal services (127.0.0.1, RFC1918 ranges, the AWS metadata endpoint
# at 169.254.169.254, etc.) and read the responses.

# Maximum number of HTTP redirects we'll follow before giving up. requests'
# default is 30 — far too generous for fetching attacker-controlled URLs.
_MAX_REDIRECTS = 5


def is_safe_target_host(hostname: str) -> bool:
    """Return True only if *every* IP `hostname` resolves to is publicly routable.

    Used both before issuing the initial request and after each redirect so an
    attacker can't bounce us off a public host into RFC1918 space.
    """
    if not hostname:
        return False
    # Strip brackets from IPv6 literals (e.g. "[::1]" → "::1")
    h = hostname.strip("[]")
    try:
        infos = socket.getaddrinfo(h, None)
    except socket.gaierror:
        return False
    except Exception:
        return False
    if not infos:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            return False
    return True

# Random User-Agents Pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",  # Tor Browser (Standard)
]

def get_random_headers():
    """สร้าง Headers ที่สมจริงและสุ่ม User-Agent"""
    user_agent = random.choice(USER_AGENTS)
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "DNT": "1",
        "Cache-Control": "max-age=0",
    }

def _fetch_with_ssrf_guard(target_url, headers, timeout):
    """GET target_url, manually following redirects so each hop is re-validated.

    Why manual: requests.get(allow_redirects=True) blindly follows 3xx Location
    headers — an attacker-controlled public host could redirect us to
    http://10.0.0.1/secret and we'd happily fetch it. We disable auto-redirects
    and re-check the host on every hop.
    """
    session = requests.Session()
    current_url = target_url
    hops = 0
    while True:
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https"):
            print(f"[SSRF GUARD] Refusing non-http(s) scheme: {parsed.scheme}")
            return None
        if not is_safe_target_host(parsed.hostname):
            print(f"[SSRF GUARD] Refusing private/loopback host: {parsed.hostname}")
            return None

        response = session.get(
            current_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
            verify=False,
        )
        if not response.is_redirect:
            return response
        if hops >= _MAX_REDIRECTS:
            print(f"[SSRF GUARD] Redirect limit ({_MAX_REDIRECTS}) hit at {current_url}")
            return response
        location = response.headers.get("Location")
        if not location:
            return response
        current_url = urljoin(current_url, location)
        hops += 1


def is_URL_accessible(url, timeout=10):
    """
    Checks if a URL is accessible and returns the result, the final URL used (if accessible), and the response object.
    This version ignores SSL certificate verification errors and uses random User-Agent to avoid blocking.
    """
    def check_url(target_url_param):
        target_url = target_url_param
        print(f"Checking URL: {target_url}")
        page = None
        parsed = urlparse(target_url)

        if not parsed.scheme:
            target_url = "https://" + target_url
            print(f"Added scheme: {target_url}")

        headers = get_random_headers()
        print(f"Using User-Agent: {headers['User-Agent'][:50]}...")

        current_url_attempt = target_url
        try:
            page = _fetch_with_ssrf_guard(current_url_attempt, headers, timeout)
            if page is None:
                return False, None, None
            print(f"Attempt 1: Accessed {current_url_attempt}, Status: {page.status_code}")

        except requests.RequestException as e:
            print(f"Attempt 1 failed for {current_url_attempt}: {e}")
            parsed_current = urlparse(current_url_attempt)
            if parsed_current.netloc and not parsed_current.netloc.startswith("www."):
                new_netloc_with_www = "www." + parsed_current.netloc
                target_url_retry = f"https://{new_netloc_with_www}{parsed_current.path or ''}{'?' + parsed_current.query if parsed_current.query else ''}"
                print(f"Retrying with www: {target_url_retry}")
                try:
                    headers_retry = get_random_headers()
                    page = _fetch_with_ssrf_guard(target_url_retry, headers_retry, timeout)
                    if page is None:
                        return False, None, None
                    print(f"Attempt 2: Accessed {target_url_retry}, Status: {page.status_code}")
                    current_url_attempt = target_url_retry
                except requests.RequestException as e_retry:
                    print(f"Attempt 2 failed for {target_url_retry}: {e_retry}")
                    return False, None, None
            else:
                return False, None, None

        if page is None:
            print(f"Page object is None after attempts for {target_url_param}")
            return False, None, None

        actual_status_code = page.status_code
        final_url_used = page.url

        # เงื่อนไข: ถ้า status code อยู่ในช่วง 200-399 (สำเร็จ หรือ redirect) ถือว่าเข้าถึงได้
        if 200 <= actual_status_code < 404:
            print(f"URL considered ACCESSIBLE based on status code: {final_url_used} (Status: {actual_status_code})")
            return True, final_url_used, page
        else:
            print(f"URL considered NOT ACCESSIBLE. Final Status: {actual_status_code}")
            return False, final_url_used, page

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(check_url, url)
        try:
            return future.result(timeout=timeout + 2)
        except concurrent.futures.TimeoutError:
            print(f"Skipping {url} due to overall timeout.")
            return False, None, None
        except Exception as e:
            print(f"An error occurred in ThreadPoolExecutor for {url}: {e}")
            return False, None, None

def get_domain(url):
    ## >> [แก้ไข] << ## ใช้ tldextract ที่ import มา และแก้ไขการคืนค่าเล็กน้อย
    extracted = tldextract.extract(url)
    hostname = f"{extracted.subdomain}.{extracted.domain}.{extracted.suffix}".strip('.')
    path = urlparse(url).path
    return hostname, extracted.domain, path


def getPageContent(url):
    # ไม่ต้อง parse และสร้าง url ใหม่ เพราะอาจทำให้ path หายไป ## >> [แก้ไข] << ##
    try:
        page = _fetch_with_ssrf_guard(url, {}, 10)
        if page is None:
            return None, None

        ## >> [แก้ไข] << ## เปลี่ยนเงื่อนไขการตรวจสอบ status code ให้กว้างขึ้น
        if not (200 <= page.status_code < 300): # สำหรับ content ต้องเป็น 2xx เท่านั้น
             raise requests.RequestException(f"Status code was {page.status_code}")

    except requests.RequestException as e: ## >> [แก้ไข] << ## ระบุ Exception ให้ชัดเจน
        print(f"Initial request for content failed: {e}")
        parsed = urlparse(url)
        if not parsed.netloc.startswith("www"):
            retry_url = f"{parsed.scheme or 'https'}://www.{parsed.netloc}{parsed.path or ''}{'?' + parsed.query if parsed.query else ''}"
            print(f"Retrying getPageContent with: {retry_url}")
            try:
                page = _fetch_with_ssrf_guard(retry_url, {}, 10)
                if page is None:
                    return None, None
            except requests.RequestException as e_retry:
                print(f"Retry for content failed: {e_retry}")
                return None, None
        else:
            return None, None

    ## >> [แก้ไข] << ## ย้ายการตรวจสอบ status มาไว้ใน try-except เพื่อให้ครอบคลุม
    if 200 <= page.status_code < 404:
        return page.url, page.content
    else:
        return None, None


#################################################################################################################################
#              Data Extraction Process
#################################################################################################################################


def extract_data_from_URL(
    hostname,
    content,
    domain,
    Href,
    Link,
    Anchor,
    Media,
    Form,
    CSS,
    Favicon,
    IFrame,
    Title,
    Text,
):
    Null_format = [
        "",
        "#",
        "#nothing",
        "#doesnotexist",
        "#null",
        "#void",
        "#whatever",
        "#content",
        "javascript::void(0)",
        "javascript::void(0);",
        "javascript::;",
        "javascript",
    ]

    soup = BeautifulSoup(content, "html.parser", from_encoding="iso-8859-1")

    # collect all external and internal hrefs from url
    for href in soup.find_all("a", href=True):
        dots = [x.start(0) for x in re.finditer("\.", href["href"])]
        if (
            hostname in href["href"]
            or domain in href["href"]
            or len(dots) == 1
            or not href["href"].startswith("http")
        ):
            if (
                "#" in href["href"]
                or "javascript" in href["href"].lower()
                or "mailto" in href["href"].lower()
            ):
                Anchor["unsafe"].append(href["href"])
            if not href["href"].startswith("http"):
                if not href["href"].startswith("/"):
                    Href["internals"].append(hostname + "/" + href["href"])
                elif href["href"] in Null_format:
                    Href["null"].append(href["href"])
                else:
                    Href["internals"].append(hostname + href["href"])
        else:
            Href["externals"].append(href["href"])
            Anchor["safe"].append(href["href"])

    # collect all media src tags
    for img in soup.find_all("img", src=True):
        dots = [x.start(0) for x in re.finditer("\.", img["src"])]
        if (
            hostname in img["src"]
            or domain in img["src"]
            or len(dots) == 1
            or not img["src"].startswith("http")
        ):
            if not img["src"].startswith("http"):
                if not img["src"].startswith("/"):
                    Media["internals"].append(hostname + "/" + img["src"])
                elif img["src"] in Null_format:
                    Media["null"].append(img["src"])
                else:
                    Media["internals"].append(hostname + img["src"])
        else:
            Media["externals"].append(img["src"])

    for audio in soup.find_all("audio", src=True):
        dots = [x.start(0) for x in re.finditer("\.", audio["src"])]
        if (
            hostname in audio["src"]
            or domain in audio["src"]
            or len(dots) == 1
            or not audio["src"].startswith("http")
        ):
            if not audio["src"].startswith("http"):
                if not audio["src"].startswith("/"):
                    Media["internals"].append(hostname + "/" + audio["src"])
                elif audio["src"] in Null_format:
                    Media["null"].append(audio["src"])
                else:
                    Media["internals"].append(hostname + audio["src"])
        else:
            Media["externals"].append(audio["src"])

    for embed in soup.find_all("embed", src=True):
        dots = [x.start(0) for x in re.finditer("\.", embed["src"])]
        if (
            hostname in embed["src"]
            or domain in embed["src"]
            or len(dots) == 1
            or not embed["src"].startswith("http")
        ):
            if not embed["src"].startswith("http"):
                if not embed["src"].startswith("/"):
                    Media["internals"].append(hostname + "/" + embed["src"])
                elif embed["src"] in Null_format:
                    Media["null"].append(embed["src"])
                else:
                    Media["internals"].append(hostname + embed["src"])
        else:
            Media["externals"].append(embed["src"])

    for i_frame in soup.find_all("iframe", src=True):
        dots = [x.start(0) for x in re.finditer("\.", i_frame["src"])]
        if (
            hostname in i_frame["src"]
            or domain in i_frame["src"]
            or len(dots) == 1
            or not i_frame["src"].startswith("http")
        ):
            if not i_frame["src"].startswith("http"):
                if not i_frame["src"].startswith("/"):
                    Media["internals"].append(hostname + "/" + i_frame["src"])
                elif i_frame["src"] in Null_format:
                    Media["null"].append(i_frame["src"])
                else:
                    Media["internals"].append(hostname + i_frame["src"])
        else:
            Media["externals"].append(i_frame["src"])

    # collect all link tags
    for link in soup.findAll("link", href=True):
        dots = [x.start(0) for x in re.finditer("\.", link["href"])]
        if (
            hostname in link["href"]
            or domain in link["href"]
            or len(dots) == 1
            or not link["href"].startswith("http")
        ):
            if not link["href"].startswith("http"):
                if not link["href"].startswith("/"):
                    Link["internals"].append(hostname + "/" + link["href"])
                elif link["href"] in Null_format:
                    Link["null"].append(link["href"])
                else:
                    Link["internals"].append(hostname + link["href"])
        else:
            Link["externals"].append(link["href"])

    for script in soup.find_all("script", src=True):
        dots = [x.start(0) for x in re.finditer("\.", script["src"])]
        if (
            hostname in script["src"]
            or domain in script["src"]
            or len(dots) == 1
            or not script["src"].startswith("http")
        ):
            if not script["src"].startswith("http"):
                if not script["src"].startswith("/"):
                    Link["internals"].append(hostname + "/" + script["src"])
                elif script["src"] in Null_format:
                    Link["null"].append(script["src"])
                else:
                    Link["internals"].append(hostname + script["src"])
        else:
            Link["externals"].append(link["href"])

    # collect all css
    for link in soup.find_all("link", rel="stylesheet"):
        dots = [x.start(0) for x in re.finditer("\.", link["href"])]
        if (
            hostname in link["href"]
            or domain in link["href"]
            or len(dots) == 1
            or not link["href"].startswith("http")
        ):
            if not link["href"].startswith("http"):
                if not link["href"].startswith("/"):
                    CSS["internals"].append(hostname + "/" + link["href"])
                elif link["href"] in Null_format:
                    CSS["null"].append(link["href"])
                else:
                    CSS["internals"].append(hostname + link["href"])
        else:
            CSS["externals"].append(link["href"])

    for style in soup.find_all("style", type="text/css"):
        try:
            start = str(style[0]).index("@import url(")
            end = str(style[0]).index(")")
            css = str(style[0])[start + 12 : end]
            dots = [x.start(0) for x in re.finditer("\.", css)]
            if (
                hostname in css
                or domain in css
                or len(dots) == 1
                or not css.startswith("http")
            ):
                if not css.startswith("http"):
                    if not css.startswith("/"):
                        CSS["internals"].append(hostname + "/" + css)
                    elif css in Null_format:
                        CSS["null"].append(css)
                    else:
                        CSS["internals"].append(hostname + css)
            else:
                CSS["externals"].append(css)
        except:
            continue

    # collect all form actions
    for form in soup.findAll("form", action=True):
        dots = [x.start(0) for x in re.finditer("\.", form["action"])]
        if (
            hostname in form["action"]
            or domain in form["action"]
            or len(dots) == 1
            or not form["action"].startswith("http")
        ):
            if not form["action"].startswith("http"):
                if not form["action"].startswith("/"):
                    Form["internals"].append(hostname + "/" + form["action"])
                elif form["action"] in Null_format or form["action"] == "about:blank":
                    Form["null"].append(form["action"])
                else:
                    Form["internals"].append(hostname + form["action"])
        else:
            Form["externals"].append(form["action"])

    # collect all link tags
    for head in soup.find_all("head"):
        for head.link in soup.find_all("link", href=True):
            dots = [x.start(0) for x in re.finditer("\.", head.link["href"])]
            if (
                hostname in head.link["href"]
                or len(dots) == 1
                or domain in head.link["href"]
                or not head.link["href"].startswith("http")
            ):
                if not head.link["href"].startswith("http"):
                    if not head.link["href"].startswith("/"):
                        Favicon["internals"].append(hostname + "/" + head.link["href"])
                    elif head.link["href"] in Null_format:
                        Favicon["null"].append(head.link["href"])
                    else:
                        Favicon["internals"].append(hostname + head.link["href"])
            else:
                Favicon["externals"].append(head.link["href"])

        for head.link in soup.findAll("link", {"href": True, "rel": True}):
            isicon = False
            if isinstance(head.link["rel"], list):
                for e_rel in head.link["rel"]:
                    if e_rel.endswith("icon"):
                        isicon = True
            else:
                if head.link["rel"].endswith("icon"):
                    isicon = True

            if isicon:
                dots = [x.start(0) for x in re.finditer("\.", head.link["href"])]
                if (
                    hostname in head.link["href"]
                    or len(dots) == 1
                    or domain in head.link["href"]
                    or not head.link["href"].startswith("http")
                ):
                    if not head.link["href"].startswith("http"):
                        if not head.link["href"].startswith("/"):
                            Favicon["internals"].append(
                                hostname + "/" + head.link["href"]
                            )
                        elif head.link["href"] in Null_format:
                            Favicon["null"].append(head.link["href"])
                        else:
                            Favicon["internals"].append(hostname + head.link["href"])
                else:
                    Favicon["externals"].append(head.link["href"])

    # collect i_frame
    for i_frame in soup.find_all("iframe", width=True, height=True, frameborder=True):
        if (
            i_frame["width"] == "0"
            and i_frame["height"] == "0"
            and i_frame["frameborder"] == "0"
        ):
            IFrame["invisible"].append(i_frame)
        else:
            IFrame["visible"].append(i_frame)
    for i_frame in soup.find_all("iframe", width=True, height=True, border=True):
        if (
            i_frame["width"] == "0"
            and i_frame["height"] == "0"
            and i_frame["border"] == "0"
        ):
            IFrame["invisible"].append(i_frame)
        else:
            IFrame["visible"].append(i_frame)
    for i_frame in soup.find_all("iframe", width=True, height=True, style=True):
        if (
            i_frame["width"] == "0"
            and i_frame["height"] == "0"
            and i_frame["style"] == "border:none;"
        ):
            IFrame["invisible"].append(i_frame)
        else:
            IFrame["visible"].append(i_frame)

    # get page title
    try:
        Title = soup.title.string
    except:
        pass

    # get content text
    Text = soup.get_text()

    return Href, Link, Anchor, Media, Form, CSS, Favicon, IFrame, Title, Text


#################################################################################################################################
#              Calculate features from extracted data
#################################################################################################################################


def extract_features(url):

    def words_raw_extraction(domain, subdomain, path):
        w_domain = re.split("\-|\.|\/|\?|\=|\@|\&|\%|\:|\_", domain.lower())
        w_subdomain = re.split("\-|\.|\/|\?|\=|\@|\&|\%|\:|\_", subdomain.lower())
        w_path = re.split("\-|\.|\/|\?|\=|\@|\&|\%|\:|\_", path.lower())
        raw_words = w_domain + w_path + w_subdomain
        w_host = w_domain + w_subdomain
        raw_words = list(filter(None, raw_words))
        return raw_words, list(filter(None, w_host)), list(filter(None, w_path))

    Href = {"internals": [], "externals": [], "null": []}
    Link = {"internals": [], "externals": [], "null": []}
    Anchor = {"safe": [], "unsafe": [], "null": []}
    Media = {"internals": [], "externals": [], "null": []}
    Form = {"internals": [], "externals": [], "null": []}
    CSS = {"internals": [], "externals": [], "null": []}
    Favicon = {"internals": [], "externals": [], "null": []}
    IFrame = {"visible": [], "invisible": [], "null": []}
    Title = ""
    Text = ""
    state, iurl, page = is_URL_accessible(url)
    if state:
        content = page.content
        hostname, domain, path = get_domain(url)
        extracted_domain = tldextract.extract(url)
        domain = extracted_domain.domain + "." + extracted_domain.suffix
        subdomain = extracted_domain.subdomain
        tmp = url[url.find(extracted_domain.suffix) : len(url)]
        pth = tmp.partition("/")
        path = pth[1] + pth[2]
        words_raw, words_raw_host, words_raw_path = words_raw_extraction(
            extracted_domain.domain, subdomain, pth[2]
        )
        tld = extracted_domain.suffix
        parsed = urlparse(url)
        scheme = parsed.scheme

        Href, Link, Anchor, Media, Form, CSS, Favicon, IFrame, Title, Text = (
            extract_data_from_URL(
                hostname,
                content,
                domain,
                Href,
                Link,
                Anchor,
                Media,
                Form,
                CSS,
                Favicon,
                IFrame,
                Title,
                Text,
            )
        )

        row = [
            # url,
            # url-based features
            urlfe.url_length(url),
            urlfe.url_length(hostname),
            urlfe.having_ip_address(url),
            urlfe.count_dots(url),
            urlfe.count_hyphens(url),
            urlfe.count_at(url),
            urlfe.count_exclamation(url),
            urlfe.count_and(url),
            urlfe.count_or(url),
            urlfe.count_equal(url),
            urlfe.count_underscore(url),
            urlfe.count_tilde(url),
            urlfe.count_percentage(url),
            urlfe.count_slash(url),
            urlfe.count_star(url),
            urlfe.count_colon(url),
            urlfe.count_comma(url),
            urlfe.count_semicolumn(url),
            urlfe.count_dollar(url),
            urlfe.count_space(url),
            urlfe.check_www(words_raw),
            urlfe.check_com(words_raw),
            urlfe.count_double_slash(url),
            urlfe.count_http_token(path),
            urlfe.https_token(scheme),
            urlfe.ratio_digits(url),
            urlfe.ratio_digits(hostname),
            urlfe.punycode(url),
            urlfe.port(url),
            urlfe.tld_in_path(tld, path),
            urlfe.tld_in_subdomain(tld, subdomain),
            urlfe.abnormal_subdomain(url),
            urlfe.count_subdomain(url),
            urlfe.prefix_suffix(url),
            urlfe.random_domain(domain),
            urlfe.shortening_service(url),
            urlfe.path_extension(path),
            urlfe.count_redirection(page),
            urlfe.count_external_redirection(page, domain),
            urlfe.length_word_raw(words_raw),
            urlfe.char_repeat(words_raw),
            urlfe.shortest_word_length(words_raw),
            urlfe.shortest_word_length(words_raw_host),
            urlfe.shortest_word_length(words_raw_path),
            urlfe.longest_word_length(words_raw),
            urlfe.longest_word_length(words_raw_host),
            urlfe.longest_word_length(words_raw_path),
            urlfe.average_word_length(words_raw),
            urlfe.average_word_length(words_raw_host),
            urlfe.average_word_length(words_raw_path),
            urlfe.phish_hints(url),
            urlfe.domain_in_brand(extracted_domain.domain),
            urlfe.brand_in_path(extracted_domain.domain, subdomain),
            urlfe.suspecious_tld(tld),
            urlfe.statistical_report(url, domain),
            # # content-based features
            ctnfe.nb_hyperlinks(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.internal_hyperlinks(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.external_hyperlinks(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.null_hyperlinks(hostname, Href, Link, Media, Form, CSS, Favicon),
            ctnfe.external_css(CSS),
            ctnfe.internal_redirection(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.external_redirection(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.internal_errors(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.external_errors(Href, Link, Media, Form, CSS, Favicon),
            ctnfe.login_form(Form),
            ctnfe.external_favicon(Favicon),
            ctnfe.links_in_tags(Link),
            ctnfe.submitting_to_email(Form),
            ctnfe.internal_media(Media),
            ctnfe.external_media(Media),
            # additional content-based features
            ctnfe.sfh(hostname, Form),
            ctnfe.iframe(IFrame),
            ctnfe.popup_window(Text),
            ctnfe.safe_anchor(Anchor),
            ctnfe.onmouseover(Text),
            ctnfe.right_clic(Text),
            ctnfe.empty_title(Title),
            ctnfe.domain_in_title(extracted_domain.domain, Title),
            ctnfe.domain_with_copyright(extracted_domain.domain, Text),
            # # thirs-party-based features
            trdfe.whois_registered_domain(domain),
            trdfe.domain_registration_length(domain),
            trdfe.domain_age(domain),
            trdfe.web_traffic(url),
            trdfe.dns_record(domain),
            trdfe.google_index(url),
            trdfe.page_rank(key, domain),
            # status
        ]
        # print(row)
        return row
    return None
