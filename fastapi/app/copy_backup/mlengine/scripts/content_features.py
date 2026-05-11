import requests
import re


#################################################################################################################################
#               Number of hyperlinks present in a website (Kumar Jain'18)
#################################################################################################################################

def nb_hyperlinks(Href, Link, Media, Form, CSS, Favicon):
    try:
        return len(Href['internals']) + len(Href['externals']) + \
               len(Link['internals']) + len(Link['externals']) + \
               len(Media['internals']) + len(Media['externals']) + \
               len(Form['internals']) + len(Form['externals']) + \
               len(CSS['internals']) + len(CSS['externals']) + \
               len(Favicon['internals']) + len(Favicon['externals'])
    except Exception:
        return 1  # Return 1 in case of an error


# def nb_hyperlinks(dom):
#     return len(dom.find("href")) + len(dom.find("src"))

#################################################################################################################################
#               Internal hyperlinks ratio (Kumar Jain'18)
#################################################################################################################################


def h_total(Href, Link, Media, Form, CSS, Favicon):
    try:
        return nb_hyperlinks(Href, Link, Media, Form, CSS, Favicon)
    except Exception:
        return 1  # Return 1 in case of an error

def h_internal(Href, Link, Media, Form, CSS, Favicon):
    try:
        return len(Href['internals']) + len(Link['internals']) + len(Media['internals']) + \
               len(Form['internals']) + len(CSS['internals']) + len(Favicon['internals'])
    except Exception:
        return 1  # Return 1 in case of an error

def internal_hyperlinks(Href, Link, Media, Form, CSS, Favicon):
    try:
        total = h_total(Href, Link, Media, Form, CSS, Favicon)
        if total == 0:
            return 0
        else:
            return h_internal(Href, Link, Media, Form, CSS, Favicon) / total
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               External hyperlinks ratio (Kumar Jain'18)
#################################################################################################################################


def h_external(Href, Link, Media, Form, CSS, Favicon):
    try:
        return len(Href['externals']) + len(Link['externals']) + len(Media['externals']) + \
               len(Form['externals']) + len(CSS['externals']) + len(Favicon['externals'])
    except Exception:
        return 1  # Return 1 in case of an error

def external_hyperlinks(Href, Link, Media, Form, CSS, Favicon):
    try:
        total = h_total(Href, Link, Media, Form, CSS, Favicon)
        if total == 0:
            return 0
        else:
            return h_external(Href, Link, Media, Form, CSS, Favicon) / total
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Number of null hyperlinks (Kumar Jain'18)
#################################################################################################################################

def h_null(hostname, Href, Link, Media, Form, CSS, Favicon):
    try:
        return len(Href['null']) + len(Link['null']) + len(Media['null']) + \
               len(Form['null']) + len(CSS['null']) + len(Favicon['null'])
    except Exception:
        return 1  # Return 1 in case of an error

def null_hyperlinks(hostname, Href, Link, Media, Form, CSS, Favicon):
    try:
        total = h_total(Href, Link, Media, Form, CSS, Favicon)
        if total == 0:
            return 0
        return h_null(hostname, Href, Link, Media, Form, CSS, Favicon) / total
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Extrenal CSS (Kumar Jain'18)
#################################################################################################################################


def external_css(CSS):
    try:
        return len(CSS['externals'])
    except Exception:
        return 1  # Return 1 in case of an error

    

#################################################################################################################################
#               Internal redirections (Kumar Jain'18)
#################################################################################################################################


import requests

def h_i_redirect(Href, Link, Media, Form, CSS, Favicon):
    try:
        count = 0
        for link in Href['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Link['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Media['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Form['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in CSS['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Favicon['internals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        return count
    except Exception:
        return 1

def internal_redirection(Href, Link, Media, Form, CSS, Favicon):
    try:
        internals = h_internal(Href, Link, Media, Form, CSS, Favicon)
        if internals > 0:
            return h_i_redirect(Href, Link, Media, Form, CSS, Favicon) / internals
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               External redirections (Kumar Jain'18)
#################################################################################################################################


import requests

def h_e_redirect(Href, Link, Media, Form, CSS, Favicon):
    try:
        count = 0
        for link in Href['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Link['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Media['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Form['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in CSS['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        for link in Favicon['externals']:
            try:
                r = requests.get(link, timeout=20)
                if len(r.history) > 0:
                    count += 1
            except Exception:
                continue
        return count
    except Exception:
        return 1

def external_redirection(Href, Link, Media, Form, CSS, Favicon):
    try:
        externals = h_external(Href, Link, Media, Form, CSS, Favicon)
        if externals > 0:
            return h_e_redirect(Href, Link, Media, Form, CSS, Favicon) / externals
        return 0
    except Exception:
        return 1  # Return 1 in case of an error




#################################################################################################################################
#               Generates internal errors (Kumar Jain'18)
#################################################################################################################################

import requests

def h_i_error(Href, Link, Media, Form, CSS, Favicon):
    try:
        count = 0
        for link in Href['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Link['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Media['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Form['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in CSS['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Favicon['internals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        return count
    except Exception:
        return 1

def internal_errors(Href, Link, Media, Form, CSS, Favicon):
    try:
        internals = h_internal(Href, Link, Media, Form, CSS, Favicon)
        if internals > 0:
            return h_i_error(Href, Link, Media, Form, CSS, Favicon) / internals
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Generates external errors (Kumar Jain'18)
#################################################################################################################################


import requests

def h_e_error(Href, Link, Media, Form, CSS, Favicon):
    try:
        count = 0
        for link in Href['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Link['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Media['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Form['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in CSS['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        for link in Favicon['externals']:
            try:
                if requests.get(link, timeout=20).status_code >= 400:
                    count += 1
            except Exception:
                continue
        return count
    except Exception:
        return 1

def external_errors(Href, Link, Media, Form, CSS, Favicon):
    try:
        externals = h_external(Href, Link, Media, Form, CSS, Favicon)
        if externals > 0:
            return h_e_error(Href, Link, Media, Form, CSS, Favicon) / externals
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Having login form link (Kumar Jain'18)
#################################################################################################################################

import re

def login_form(Form):
    try:
        p = re.compile('([a-zA-Z0-9\_])+.php')
        if len(Form['externals']) > 0 or len(Form['null']) > 0:
            return 1
        for form in Form['internals'] + Form['externals']:
            if p.match(form) is not None:
                return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Having external favicon (Kumar Jain'18)
#################################################################################################################################

def external_favicon(Favicon):
    try:
        if len(Favicon['externals']) > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#               Submitting to email 
#################################################################################################################################

def submitting_to_email(Form):
    try:
        for form in Form['internals'] + Form['externals']:
            if "mailto:" in form or "mail()" in form:
                return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Percentile of internal media <= 61 : Request URL in Zaini'2019 
#################################################################################################################################

def internal_media(Media):
    try:
        total = len(Media['internals']) + len(Media['externals'])
        internals = len(Media['internals'])
        percentile = (internals / float(total)) * 100 if total > 0 else 0
    except Exception:
        return 1  # Return 1 in case of an error
    
    return percentile


#################################################################################################################################
#               Percentile of external media : Request URL in Zaini'2019 
#################################################################################################################################

def external_media(Media):
    try:
        total = len(Media['internals']) + len(Media['externals'])
        externals = len(Media['externals'])
        percentile = (externals / float(total)) * 100 if total > 0 else 0
    except Exception:
        return 1  # Return 1 in case of an error
    
    return percentile

#################################################################################################################################
#               Check for empty title 
#################################################################################################################################

def empty_title(Title):
    try:
        if Title:
            return 0
        return 1
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#               Percentile of safe anchor : URL_of_Anchor in Zaini'2019 (Kumar Jain'18)
#################################################################################################################################

def safe_anchor(Anchor):
    try:
        total = len(Anchor['safe']) + len(Anchor['unsafe'])
        unsafe = len(Anchor['unsafe'])
        percentile = (unsafe / float(total)) * 100 if total > 0 else 0
    except Exception:
        return 1  # Return 1 in case of an error
    
    return percentile


#################################################################################################################################
#               Percentile of internal links : links_in_tags in Zaini'2019 but without <Meta> tag
#################################################################################################################################

def links_in_tags(Link):
    try:
        total = len(Link['internals']) + len(Link['externals'])
        internals = len(Link['internals'])
        percentile = (internals / float(total)) * 100 if total > 0 else 0
    except Exception:
        return 1  # Return 1 in case of an error
    
    return percentile


#################################################################################################################################
#              Server Form Handler  : sfh in Zaini'2019
#################################################################################################################################

def sfh(hostname, Form):
    try:
        if len(Form['null']) > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case


#################################################################################################################################
#              IFrame Redirection
#################################################################################################################################

def iframe(IFrame):
    try:
        if len(IFrame['invisible']) > 0:
            return 1
        return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#              Onmouse action
#################################################################################################################################

def onmouseover(content):
    try:
        if 'onmouseover="window.status=' in str(content).lower().replace(" ",""):
            return 1
        else:
            return 0
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#              Pop up window
#################################################################################################################################

def popup_window(content):
    try:
        if "prompt(" in str(content).lower():
            return 1
        else:
            return 0
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#              Right_clic action
#################################################################################################################################

import re

def right_clic(content):
    try:
        if re.findall(r"event.button ?== ?2", content):
            return 1
        else:
            return 0
    except Exception:
        return 1  # Return 1 in case of an error



#################################################################################################################################
#              Domain in page title (Shirazi'18)
#################################################################################################################################

def domain_in_title(domain, title):
    try:
        if domain.lower() in title.lower(): 
            return 0
        return 1
    except Exception:
        return 1  # Return 1 in case of an error


#################################################################################################################################
#              Domain after copyright logo (Shirazi'18)
#################################################################################################################################

import re

def domain_with_copyright(domain, content):
    try:
        m = re.search(u'(\N{COPYRIGHT SIGN}|\N{TRADE MARK SIGN}|\N{REGISTERED SIGN})', content)
        if m:  # Check if match is found
            _copyright = content[m.span()[0]-50:m.span()[0]+50]
            if domain.lower() in _copyright.lower():
                return 0
            else:
                return 1
        return 0  # Return 0 if no copyright symbol is found
    except Exception:
        return 1  # Return 1 in case of any error

