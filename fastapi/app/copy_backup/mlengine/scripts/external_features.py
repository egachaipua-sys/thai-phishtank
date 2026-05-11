#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 17:58:48 2020

@author: hannousse
"""
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import whois
import time
import re


#################################################################################################################################
#               Domain registration age 
#################################################################################################################################

def domain_registration_length(domain):
    try:
        res = whois.whois(domain)
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
        host = whois.whois(domain)
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
        hostname = whois.whois(domain).domain_name
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
    try:
        rank = BeautifulSoup(urllib.request.urlopen("http://data.alexa.com/data?cli=10&dat=s&url=" + short_url, timeout=20).read(), "xml").find("REACH")['RANK']
        return int(rank)
    except Exception:
        return 1

#################################################################################################################################
#               Domain age of a url
#################################################################################################################################

def domain_age(domain):
    try:
        url = domain.split("//")[-1].split("/")[0].split('?')[0]
        w = whois.whois(url)
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
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
        headers = {'User-Agent': user_agent}
        query = {'q': 'site:' + url}
        google = "https://www.google.com/search?" + urlencode(query)
        data = requests.get(google, headers=headers, timeout=20)
        data.encoding = 'ISO-8859-1'
        soup = BeautifulSoup(data.content, "html.parser")
        if 'Our systems have detected unusual traffic from your computer network.' in str(soup):
            return -1
        return 0 if soup.find(id="rso") else 1
    except Exception:
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

