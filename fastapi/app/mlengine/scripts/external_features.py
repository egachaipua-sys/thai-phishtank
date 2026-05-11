#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 17:58:48 2020

@author: hannousse
"""
from datetime import datetime
from bs4 import BeautifulSoup
from cachetools import TTLCache
import requests
import tldextract
import whois
import time
import re


#################################################################################################################################
#               Shared WHOIS cache
#################################################################################################################################
# A single API request triggers WHOIS lookups from three feature functions
# (whois_registered_domain, domain_registration_length, domain_age) plus up to
# two more from the request handler. Without sharing, that's 5+ round trips
# (5-10s each) for one URL. Memoise by registered domain so all callers in the
# same request — and across requests within the TTL — collapse to one lookup.

_WHOIS_CACHE = TTLCache(maxsize=1000, ttl=3600)
_WHOIS_SENTINEL = object()


def cached_whois(target):
    """`whois.whois(target)` memoised by registered domain.

    Re-raises a cached exception if the previous lookup failed, preserving the
    original error-handling contract.
    """
    ext = tldextract.extract(target)
    if not ext.domain or not ext.suffix:
        return whois.whois(target)
    key = f"{ext.domain}.{ext.suffix}".lower()
    cached = _WHOIS_CACHE.get(key, _WHOIS_SENTINEL)
    if cached is not _WHOIS_SENTINEL:
        if isinstance(cached, BaseException):
            raise cached
        return cached
    try:
        result = whois.whois(key)
    except BaseException as exc:
        _WHOIS_CACHE[key] = exc
        raise
    _WHOIS_CACHE[key] = result
    return result


#################################################################################################################################
#               Domain registration age
#################################################################################################################################

def domain_registration_length(domain):
    try:
        res = cached_whois(domain)
        expiration_date = res.expiration_date
        today = datetime.today()
        if expiration_date:
            if isinstance(expiration_date, list):
                expiration_date = min(expiration_date)
            return abs((expiration_date - today).days)
        return 0
    except Exception:
        return 1

def domain_registration_length1(domain):
    try:
        v1 = -1
        v2 = -1
        host = cached_whois(domain)
        hostname = host.domain_name
        expiration_date = host.expiration_date
        today = datetime.today()
        if isinstance(hostname, list):
            v1 = 1 if all(not re.search(h.lower(), domain) for h in hostname) else 0
        else:
            v1 = 1 if not re.search(hostname.lower(), domain) else 0
        if expiration_date:
            if isinstance(expiration_date, list):
                expiration_date = min(expiration_date)
            v2 = abs((expiration_date - today).days)
        return v1, v2
    except Exception:
        return 1, -1

#################################################################################################################################
#               Domain recognized by WHOIS
#################################################################################################################################


def whois_registered_domain(domain):
    try:
        hostname = cached_whois(domain).domain_name
        if isinstance(hostname, list):
            return 1 if all(not re.search(h.lower(), domain) for h in hostname) else 0
        return 1 if not re.search(hostname.lower(), domain) else 0
    except Exception:
        return 1

#################################################################################################################################
#               Unable to get web traffic (Page Rank)
#################################################################################################################################
import urllib

def web_traffic(short_url):
    # Alexa was retired in May 2022; the original implementation always raised
    # and returned 1, so the trained model already treats this as a constant.
    # Skipping avoids the 20s timeout on every cache-miss request.
    return 1

#################################################################################################################################
#               Domain age of a url
#################################################################################################################################

def domain_age(domain):
    try:
        url = domain.split("//")[-1].split("/")[0].split('?')[0]
        w = cached_whois(url)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        return (datetime.today() - creation_date).days if creation_date else 1
    except Exception:
        return 1

#################################################################################################################################
#               Global rank
#################################################################################################################################

def global_rank(domain):
    try:
        rank_checker_response = requests.post("https://www.checkpagerank.net/index.php", {"name": domain}, timeout=20)
        return int(re.findall(r"Global Rank: ([0-9]+)", rank_checker_response.text)[0])
    except Exception:
        return 1

#################################################################################################################################
#               Google index
#################################################################################################################################


from urllib.parse import urlencode

def google_index(url):
    # Google rate-limits scraping aggressively, so this almost always tripped
    # the bot detection and returned 1 after a 20s timeout. The trained model
    # is already calibrated against the constant-1 fallback.
    return 1

#print(google_index('http://www.google.com'))
#################################################################################################################################
#               DNSRecord  expiration length
#################################################################################################################################

import dns.resolver

def dns_record(domain):
    try:
        nameservers = dns.resolver.resolve(domain, 'NS')
        return 0 if len(nameservers) > 0 else 1
    except Exception:
        return 1

#################################################################################################################################
#               Page Rank from OPR
#################################################################################################################################


def page_rank(key, domain):
    try:
        url = f'https://openpagerank.com/api/v1.0/getPageRank?domains%5B0%5D={domain}'
        response = requests.get(url, headers={'API-OPR': key}, timeout=20)
        result = response.json()

        # ตรวจสอบว่าข้อมูลมีอยู่และไม่เป็นค่าว่าง
        page_rank = result.get('response', [{}])[0].get('page_rank_integer')
        if page_rank is None or page_rank == "":
            return 0  # กรณีข้อมูลเป็นค่าว่างให้คืนค่า 0
        return page_rank
    except Exception:
        return 1  # กรณีเกิดข้อผิดพลาดให้คืนค่า 1
