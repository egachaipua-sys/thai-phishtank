# 0 stands for legitimate
# 1 stands for phishing

import re


#LOCALHOST_PATH = "/var/www/html/"
HINTS = ['wp', 'login', 'includes', 'admin', 'content', 'site', 'images', 'js', 'alibaba', 'css', 'myaccount', 'dropbox', 'themes', 'plugins', 'signin', 'view']

def __txt_to_list(file_path):
    try:
        with open(file_path, "r") as txt_object:
            return [line.strip() for line in txt_object]
    except Exception:
        return 1  # Return 1 if there's an error

allbrand = __txt_to_list("data/allbrands.txt")

#print(allbrand)

#################################################################################################################################
#               Having IP address in hostname
#################################################################################################################################

def having_ip_address(url):
    try:
        match = re.search(
            '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'  # IPv4
            '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4
            '((0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\/)|'  # IPv4 in hexadecimal
            '(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}|'  # IPv6
            '[0-9a-fA-F]{7}', url)  # IPv6 shorthand
        return 1 if match else 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               URL hostname length 
#################################################################################################################################

def url_length(url):
    try:
        return len(url)
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               URL shortening
#################################################################################################################################

def shortening_service(full_url):
    try:
        match = re.search(
            'bit\\.ly|goo\\.gl|shorte\\.st|go2l\\.ink|x\\.co|ow\\.ly|t\\.co|tinyurl|tr\\.im|is\\.gd|cli\\.gs|'
            'yfrog\\.com|migre\\.me|ff\\.im|tiny\\.cc|url4\\.eu|twit\\.ac|su\\.pr|twurl\\.nl|snipurl\\.com|'
            'short\\.to|BudURL\\.com|ping\\.fm|post\\.ly|Just\\.as|bkite\\.com|snipr\\.com|fic\\.kr|loopt\\.us|'
            'doiop\\.com|short\\.ie|kl\\.am|wp\\.me|rubyurl\\.com|om\\.ly|to\\.ly|bit\\.do|t\\.co|lnkd\\.in|'
            'db\\.tt|qr\\.ae|adf\\.ly|goo\\.gl|bitly\\.com|cur\\.lv|tinyurl\\.com|ow\\.ly|bit\\.ly|ity\\.im|'
            'q\\.gs|is\\.gd|po\\.st|bc\\.vc|twitthis\\.com|u\\.to|j\\.mp|buzurl\\.com|cutt\\.us|u\\.bb|yourls\\.org|'
            'x\\.co|prettylinkpro\\.com|scrnch\\.me|filoops\\.info|vzturl\\.com|qr\\.net|1url\\.com|tweez\\.me|v\\.gd|'
            'tr\\.im|link\\.zip\\.net',
            full_url
        )
        return 1 if match else 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count at (@) symbol at base url
#################################################################################################################################

def count_at(base_url):
    try:
        return base_url.count('@')
    except Exception:
        return 1  # Return 1 in case of an error

 
#################################################################################################################################
#               Count comma (,) symbol at base url
#################################################################################################################################

def count_comma(base_url):
    try:
        return base_url.count(',')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count dollar ($) symbol at base url
#################################################################################################################################

def count_dollar(base_url):
    try:
        return base_url.count('$')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Having semicolumn (;) symbol at base url
#################################################################################################################################

def count_semicolumn(url):
    try:
        return url.count(';')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count (space, %20) symbol at base url (Das'19)
#################################################################################################################################

def count_space(base_url):
    try:
        return base_url.count(' ') + base_url.count('%20')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count and (&) symbol at base url (Das'19)
#################################################################################################################################

def count_and(base_url):
    try:
        return base_url.count('&')
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Count redirection (//) symbol at full url
#################################################################################################################################

def count_double_slash(full_url):
    try:
        positions = [x.start(0) for x in re.finditer('//', full_url)]
        if positions and positions[-1] > 6:
            return 1
        else:
            return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count slash (/) symbol at full url
#################################################################################################################################

def count_slash(full_url):
    try:
        return full_url.count('/')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count equal (=) symbol at base url
#################################################################################################################################

def count_equal(base_url):
    try:
        return base_url.count('=')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count percentage (%) symbol at base url (Chiew2019)
#################################################################################################################################

def count_percentage(base_url):
    try:
        return base_url.count('%')
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Count exclamation (?) symbol at base url
#################################################################################################################################

def count_exclamation(base_url):
    try:
        return base_url.count('?')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count underscore (_) symbol at base url
#################################################################################################################################

def count_underscore(base_url):
    try:
        return base_url.count('_')
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Count dash (-) symbol at base url
#################################################################################################################################

def count_hyphens(base_url):
    try:
        return base_url.count('-')
    except Exception:
        return 1  # Return 1 in case of an error

#################################################################################################################################
#              Count number of dots in hostname
#################################################################################################################################

def count_dots(hostname):
    try:
        return hostname.count('.')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#              Count number of colon (:) symbol
#################################################################################################################################

def count_colon(url):
    try:
        return url.count(':')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count number of stars (*) symbol (Srinivasa Rao'19)
#################################################################################################################################

def count_star(url):
    try:
        return url.count('*')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Count number of OR (|) symbol (Srinivasa Rao'19)
#################################################################################################################################

def count_or(url):
    try:
        return url.count('|')
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Path entension != .txt
#################################################################################################################################

def path_extension(url_path):
    try:
        if url_path.endswith('.txt'):
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Having multiple http or https in url path
#################################################################################################################################

def count_http_token(url_path):
    try:
        return url_path.count('http')
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Uses https protocol
#################################################################################################################################

def https_token(scheme):
    try:
        if scheme == 'https':
            return 0
        return 1
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Ratio of digits in hostname 
#################################################################################################################################

def ratio_digits(hostname):
    try:
        numeric_count = len(re.sub("[^0-9]", "", hostname))
        return numeric_count / len(hostname) if len(hostname) > 0 else 0
    except Exception:
        return 1  # Return 1 in case of an error

#################################################################################################################################
#               Count number of digits in domain/subdomain/path
#################################################################################################################################

def count_digits(line):
    try:
        return len(re.sub("[^0-9]", "", line))
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#              Checks if tilde symbol exist in webpage URL (Chiew2019)
#################################################################################################################################

def count_tilde(full_url):
    try:
        if full_url.count('~') > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               number of phish-hints in url path 
#################################################################################################################################

def phish_hints(url_path):
    try:
        count = 0
        for hint in HINTS:
            count += url_path.lower().count(hint)
        return count
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Check if TLD exists in the path 
#################################################################################################################################

def tld_in_path(tld, path):
    try:
        if path.lower().count(tld) > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               Check if tld is used in the subdomain 
#################################################################################################################################

def tld_in_subdomain(tld, subdomain):
    try:
        if subdomain.count(tld) > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Check if TLD in bad position (Chiew2019)
#################################################################################################################################

def tld_in_bad_position(tld, subdomain, path):
    try:
        if tld_in_path(tld, path) == 1 or tld_in_subdomain(tld, subdomain) == 1:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error




#################################################################################################################################
#               Abnormal subdomain starting with wwww-, wwNN
#################################################################################################################################

def abnormal_subdomain(url):
    try:
        if re.search(r'(http[s]?://(w[w]?|\d))([w]?(\d|-))', url):
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error

    

#################################################################################################################################
#               Number of redirection 
#################################################################################################################################

def count_redirection(page):
    try:
        return len(page.history)
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               Number of redirection to different domains
#################################################################################################################################

def count_external_redirection(page, domain):
    try:
        count = 0
        if len(page.history) == 0:
            return 0
        else:
            for response in page.history:
                if domain.lower() not in response.url.lower():
                    count += 1
            return count
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               Is the registered domain created with random characters (Sahingoz2019)
#################################################################################################################################

class MockNLPClass:
    def check_word_random(self, domain):
        try:
            # จำลองการตรวจสอบว่าโดเมนเป็นแบบสุ่มหรือไม่
            return 0 if len(domain) > 10 else 1  # ตัวอย่างเงื่อนไข
        except Exception:
            return 1  # Return 1 in case of an error

def random_domain(domain):
    try:
        nlp_manager = MockNLPClass()
        return nlp_manager.check_word_random(domain)
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               Consecutive Character Repeat (Sahingoz2019)
#################################################################################################################################

def char_repeat(words_raw):
    try:
        def __all_same(items):
            return all(x == items[0] for x in items)

        repeat = {'2': 0, '3': 0, '4': 0, '5': 0}
        part = [2, 3, 4, 5]

        for word in words_raw:
            for char_repeat_count in part:
                for i in range(len(word) - char_repeat_count + 1):
                    sub_word = word[i:i + char_repeat_count]
                    if __all_same(sub_word):
                        repeat[str(char_repeat_count)] += 1

        return sum(repeat.values())
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               puny code in domain (Sahingoz2019)
#################################################################################################################################

def punycode(url):
    try:
        if url.startswith("http://xn--") or url.startswith("https://xn--"):
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error

#################################################################################################################################
#               domain in brand list (Sahingoz2019)
#################################################################################################################################

def domain_in_brand(domain):
    try:
        if domain in allbrand:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error

import Levenshtein

def domain_in_brand1(domain):
    try:
        for d in allbrand:
            if len(Levenshtein.editops(domain.lower(), d.lower())) < 2:
                return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error




#################################################################################################################################
#               brand name in path (Srinivasa-Rao2019)
#################################################################################################################################

def brand_in_path(domain, path):
    try:
        for b in allbrand:
            if '.' + b + '.' in path and b not in domain:
                return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               count www in url words (Sahingoz2019)
#################################################################################################################################

def check_www(words_raw):
    try:
        count = 0
        for word in words_raw:
            if 'www' in word:
                count += 1
        return count
    except Exception:
        return 1  # Return 1 in case of an error

    
#################################################################################################################################
#               count com in url words (Sahingoz2019)
#################################################################################################################################

def check_com(words_raw):
    try:
        count = 0
        for word in words_raw:
            if 'com' in word:
                count += 1
        return count
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               check port presence in domain
#################################################################################################################################

def port(url):
    try:
        if re.search(r"^[a-z][a-z0-9+\-.]*://([a-z0-9\-._~%!$&'()*+,;=]+@)?([a-z0-9\-._~%]+|\[[a-z0-9\-._~%!$&'()*+,;=:]+\]):([0-9]+)", url):
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               length of raw word list (Sahingoz2019)
#################################################################################################################################

def length_word_raw(words_raw):
    try:
        return len(words_raw)
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               count average word length in raw word list (Sahingoz2019)
#################################################################################################################################

def average_word_length(words_raw):
    try:
        if len(words_raw) == 0:
            return 0
        return sum(len(word) for word in words_raw) / len(words_raw)
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               longest word length in raw word list (Sahingoz2019)
#################################################################################################################################

def longest_word_length(words_raw):
    try:
        if len(words_raw) == 0:
            return 0
        return max(len(word) for word in words_raw)
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               shortest word length in raw word list (Sahingoz2019)
#################################################################################################################################

def shortest_word_length(words_raw):
    try:
        if len(words_raw) == 0:
            return 0
        return min(len(word) for word in words_raw)
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               prefix suffix
#################################################################################################################################

def prefix_suffix(url):
    try:
        if re.findall(r"https?://[^\-]+-[^\-]+/", url):
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               count subdomain
#################################################################################################################################

def count_subdomain(url):
    try:
        dot_count = len(re.findall(r"\.", url))
        if dot_count == 1:
            return 1
        elif dot_count == 2:
            return 2
        else:
            return 3
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Statistical report
#################################################################################################################################

import socket
import re

def statistical_report(url, domain):
    try:
        url_match = re.search(r'at\.ua|usa\.cc|baltazarpresentes\.com\.br|pe\.hu|esy\.es|hol\.es|sweddy\.com|myjino\.ru|96\.lt|ow\.ly', url)
        ip_address = socket.gethostbyname(domain)
        ip_match = re.search(r'146\.112\.61\.108|213\.174\.157\.151|121\.50\.168\.88|192\.185\.217\.116|78\.46\.211\.158|181\.174\.165\.13|46\.242\.145\.103|121\.50\.168\.40|83\.125\.22\.219|46\.242\.145\.98|'
                            r'107\.151\.148\.44|107\.151\.148\.107|64\.70\.19\.203|199\.184\.144\.27|107\.151\.148\.108|107\.151\.148\.109|119\.28\.52\.61|54\.83\.43\.69|52\.69\.166\.231|216\.58\.192\.225|'
                            r'118\.184\.25\.86|67\.208\.74\.71|23\.253\.126\.58|104\.239\.157\.210|175\.126\.123\.219|141\.8\.224\.221|10\.10\.10\.10|43\.229\.108\.32|103\.232\.215\.140|69\.172\.201\.153|'
                            r'216\.218\.185\.162|54\.225\.104\.146|103\.243\.24\.98|199\.59\.243\.120|31\.170\.160\.61|213\.19\.128\.77|62\.113\.226\.131|208\.100\.26\.234|195\.16\.127\.102|195\.16\.127\.157|'
                            r'34\.196\.13\.28|103\.224\.212\.222|172\.217\.4\.225|54\.72\.9\.51|192\.64\.147\.141|198\.200\.56\.183|23\.253\.164\.103|52\.48\.191\.26|52\.214\.197\.72|87\.98\.255\.18|209\.99\.17\.27|'
                            r'216\.38\.62\.18|104\.130\.124\.96|47\.89\.58\.141|78\.46\.211\.158|54\.86\.225\.156|54\.82\.156\.19|37\.157\.192\.102|204\.11\.56\.48|110\.34\.231\.42', ip_address)
        
        if url_match or ip_match:
            return 1
        else:
            return 0
    except Exception:
        return 1


#################################################################################################################################
#               Suspecious TLD
#################################################################################################################################

suspecious_tlds = ['fit','tk', 'gp', 'ga', 'work', 'ml', 'date', 'wang', 'men', 'icu', 'online', 'click',  # Spamhaus
                   'country', 'stream', 'download', 'xin', 'racing', 'jetzt',
                   'ren', 'mom', 'party', 'review', 'trade', 'accountants', 
                   'science', 'work', 'ninja', 'xyz', 'faith', 'zip', 'cricket', 'win',
                   'accountant', 'realtor', 'top', 'christmas', 'gdn',  # Shady Top-Level Domains
                   'link',  # Blue Coat Systems
                   'asia', 'club', 'la', 'ae', 'exposed', 'pe', 'go.id', 'rs', 'k12.pa.us', 'or.kr',
                   'ce.ke', 'audio', 'gob.pe', 'gov.az', 'website', 'bj', 'mx', 'media', 'sa.gov.au'  # statistics
                  ]

def suspecious_tld(tld):
    try:
        if tld in suspecious_tlds:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error
